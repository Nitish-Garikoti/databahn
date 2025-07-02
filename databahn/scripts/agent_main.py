import asyncio
import json
from dataclasses import dataclass, field
from agents import Agent, Runner, function_tool
from agents.mcp import MCPServerStdio
from openai import AsyncOpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from base import openai_client
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
)
from typing import cast

from agents import Agent, Runner, function_tool
from utils.vector_search import setup_vector_db, get_embedding, find_top_k_relevant_tables
from tools.tools import MANUAL_FUNCTION_MAP
import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# create server
server_params=StdioServerParameters(
    command="python",
    args=["databahn/mcp_servers/scripts/mcp_server.py"]
    )


TOOL_DB_FILE = 'data/security_logs.db'
conn = sqlite3.connect(TOOL_DB_FILE)
table_collection = setup_vector_db(conn)
conn.close()


@dataclass
class Chat:
    # 2. Use the OpenAI message type hint
    messages: list[ChatCompletionMessageParam] = field(default_factory=list)

    # System prompt can be handled by prepending it to the messages list
    orchestrator_system_prompt: str = """You are a master SQLite assistant.
    Your job is to use the tools at your disposal to generate a tool call to extract the information required for user message. 
    and when you generate tool call make sure the sql_query will have tables only from corresponding tools <tool_description>. 
    If we need tables from more than one tool then generate the all tools which are required to access the tables"""


    response_system_prompt: str = """ you are a response generator. Take in the user message and the results from the tool calls that are dispatched."""

    async def manual_function_tools(self, query):
        query_embeddings = get_embedding(query)
        top_k_tables = find_top_k_relevant_tables(query_embeddings, table_collection, top_k=3)
        manual_function_tools_list: List[ChatCompletionToolParam] = []
        for val in MANUAL_FUNCTION_MAP.values():
            manual_function_tools_list.append(
                {
                    "type": "function",
                    "function": {
                        "name": val.name,
                        "description": val.description + f"<table_descriptions>{top_k_tables}</table_descriptions>",
                        "parameters": {
                            "type": "object",
                            "properties": val.args,
                            "required": list(val.args.keys())
                            }
                    }
                }
            )
        return manual_function_tools_list

    async def mcp_server_tools(self, session: ClientSession):
        session_tool_list = await session.list_tools()
        mcp_tools_list : list[ChatCompletionToolParam] = [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.inputSchema,
                },
            }
            for tool in session_tool_list.tools
        ]

        return mcp_tools_list


    async def process_query(self, session: ClientSession, input_query: str) -> None:


        tools_from_manual_functions = await self.manual_function_tools(input_query)
        tools_from_mcp_servers = await self.mcp_server_tools(session)
        # collect the tools
        tools_set_from_manual_functions = set([obj.get("function", {}).get("name", "") for obj in tools_from_manual_functions])
        tools_set_from_mcp_servers = set([obj.get("function", {}).get("name", "") for obj in tools_from_mcp_servers])
        # response = await session.list_tools()

        available_tools = tools_from_manual_functions + tools_from_mcp_servers

        # Prepend the system prompt to the messages list for the API call
        messages_with_system: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": self.orchestrator_system_prompt},
            *self.messages,
        ]

        # 4. Initial OpenAI API call
        res = await openai_client.chat.completions.create(
            # Using a standard OpenAI model
            model="gpt-4.1",
            max_tokens=8000,
            messages=messages_with_system,
            tools=available_tools,
            tool_choice="auto",  # Explicitly allow the model to choose tools
        )

        response_message = res.choices[0].message

        # 5. Handle OpenAI's response structure
        # Check for text response
        if response_message.content:
            print(response_message.content)
            self.messages.append(response_message)
            return

        # Check for tool calls
        tool_calls = response_message.tool_calls
        if not tool_calls:
            # Handle cases where the model returns neither text nor tool calls
            print("The model did not return a valid response.")
            return

        logger.info(f"the tool calls are:{tool_calls}")
        # Append the assistant's entire tool-use message to history
        self.messages.append(response_message)
        
        # This list will hold the tool results to be sent back to the model
        tool_results_for_next_call: list[ChatCompletionMessageParam] = []
        breakpoint()
        # 6. Execute each tool call from the response
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            # Arguments from OpenAI come as a JSON string
            tool_args_str = tool_call.function.arguments
            try:
                tool_args = json.loads(tool_args_str)
            except json.JSONDecodeError:
                print(f"Error: Invalid JSON in tool arguments: {tool_args_str}")
                continue

            if tool_name in MANUAL_FUNCTION_MAP: 
                result = await MANUAL_FUNCTION_MAP[tool_name].ainvoke(tool_args)
            elif tool_name in tools_set_from_mcp_servers:
                # Execute tool call (this part remains the same)
                result = await session.call_tool(tool_name, cast(dict, tool_args))
            else: 
                result = ""

            if result:
                # Add the tool result to our list for the next API call
                tool_results_for_next_call.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": getattr(result.content[0], "text", ""),
                    }
                )
            else:
                # Add the tool result to our list for the next API call
                tool_results_for_next_call.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": "",
                    }
                )

        # Append all tool results to the main message history
        self.messages.extend(tool_results_for_next_call)
        
        # Re-prepend the system prompt for the follow-up call
        messages_with_tool_results: list[ChatCompletionMessageParam] = [
            {"role": "system", "content": self.response_system_prompt},
            *self.messages,
        ]

        # 7. Get the next response from OpenAI after providing tool results
        final_res = await openai_client.chat.completions.create(
            model="gpt-4.1",
            max_tokens=8000,
            messages=messages_with_tool_results
        )
        
        final_message = final_res.choices[0].message
        if final_message.content:
            print(final_message.content)
            self.messages.append(final_message)


    async def chat_loop(self, session: ClientSession):
        while True:
            query = input("\nQuery: ").strip()
            if not query:
                continue

            self.messages.append(
                {
                    "role": "user",
                    "content": query,
                }
            )

            await self.process_query(session, query)

    async def run(self):
        # This connection logic remains unchanged
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the connection
                await session.initialize()

                await self.chat_loop(session)


chat = Chat()


asyncio.run(chat.run())



