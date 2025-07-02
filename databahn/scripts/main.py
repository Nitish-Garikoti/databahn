import asyncio
import json
from dataclasses import dataclass, field
# from agents import Agent, Runner, function_tool
# from agents.mcp import MCPServerStdio
from openai import AsyncOpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from base import openai_client
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
)
from typing import cast, List
from databahn.tools.tools import MANUAL_FUNCTION_MAP
import sqlite3
import logging
from databahn.scripts.agents.agent import Agent
from databahn.scripts.dispatcher import Dispatcher
from databahn.tools.tools import MANUAL_FUNCTION_MAP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ERROR_MESSAGE = "Looks like something went wrong. Please try again"

orchestrator_system_prompt_path = 'databahn/scripts/prompts/orchestrator/system_prompt.txt'
orchestrator_user_prompt_path = 'databahn/scripts/prompts/orchestrator/user_prompt.txt'

response_system_prompt_path = 'databahn/scripts/prompts/response/system_prompt.txt'
response_user_prompt_path = 'databahn/scripts/prompts/response/user_prompt.txt'


# create server
server_params=StdioServerParameters(
    command="python",
    args=["databahn/mcp_servers/scripts/mcp_server.py"]
    )


class Chat:

    def __init__(self):
        self.orchestrator_agent = Agent(orchestrator_system_prompt_path, orchestrator_user_prompt_path)
        self.response_agent = Agent(response_system_prompt_path, response_user_prompt_path)
        self.dispatcher = Dispatcher()


    async def process_query(self, input_query: str, session_list: List[ClientSession], state) -> None:

        orchestrator_res, state = await self.orchestrator_agent.process_query(input_query, session_list, state, agent_type="orchestrator")
        orchestrator_agent_res = orchestrator_res.choices[0].message

        if orchestrator_agent_res.content:
            logger.info(f"unexpected text response from orchestrator:{orchestrator_agent_res}")
            return ERROR_MESSAGE, state

        # Check for tool calls
        tool_calls = orchestrator_agent_res.tool_calls
        if not tool_calls:
            # Handle cases where the model returns neither text nor tool calls
            logger.info("The model did not return a valid response.")
            return ERROR_MESSAGE, state

        logger.info(f"the tool calls are:{tool_calls}")
        # Append the assistant's entire tool-use message to history

        state['orchestrator']['chat_history'].append({
            "role": "assistant", 
            "content": json.dumps([{tool.function.name: tool.function.arguments} for tool in tool_calls])})
        
        # This list will hold the tool results to be sent back to the model
        tool_results_for_next_call: list[ChatCompletionMessageParam] = []

        results = await self.dispatcher.dispatcher_invoke(tool_calls, session_list)

        # Append all tool results to the main message history
        state['orchestrator']['results'] = results

        response_agent_res, state = await self.response_agent.process_query(input_query, None, state, "response")

        final_response = None
        if response_agent_res and isinstance(response_agent_res.choices, list) and response_agent_res.choices:
            final_response = response_agent_res.choices[0].message
        if final_response and final_response.content:
            # logger.info(final_response.content)
            final_response_content = final_response.content
            final_response_content_chat_hist = {"role": "assistant", "content": final_response_content}
            state['response']['chat_history'].append(final_response_content_chat_hist)
            state['orchestrator']['chat_history'].append(final_response_content_chat_hist)
        else:
            final_response_content = ERROR_MESSAGE
        return final_response_content, state

    async def chat_loop(self, session: ClientSession):
        state = {"user_message": "",
        "orchestrator": {}, 
        "response": {}
        }
        while True:
            query = input("\nQuery: ").strip()
            if not query:
                continue
            state['user_message'] = query
            response, state = await self.process_query(query, [session], state)
            logger.info(f"\n{response}\n")

    async def run(self):
        # This connection logic remains unchanged
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the connection
                await session.initialize()

                await self.chat_loop(session)



if __name__ == "__main__":
    chat = Chat()
    asyncio.run(chat.run())
