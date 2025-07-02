import json
import logging
from typing import cast, List, Dict

from mcp import ClientSession
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
)
from databahn.tools.tools import MANUAL_FUNCTION_MAP
from databahn.utils.vector_search import setup_vector_db, get_embedding, find_top_k_relevant_tables, MANUAL_TOOL_TABLE_COLLECTION
from databahn.utils.file_util import ReadFile
from copy import deepcopy
import openai
from base import openai_client


logging.basicConfig(level=logging.INFO)
# Configure a logger for this module
logger = logging.getLogger(__name__)

class Agent:
    """An agent that processes queries using LLMs and a set of tools."""
    
    def __init__(self, system_prompt_path: str, user_prompt_path: str):
        """
        Initializes the Agent by loading prompts from file paths and setting up state.
        """
        self.system_prompt = ReadFile.read_file(system_prompt_path)
        self.user_prompt = ReadFile.read_file(user_prompt_path)
        
    async def _get_manual_tools(self, query: str) -> list[ChatCompletionToolParam]:
        """Generates tool definitions based on semantic search."""
        query_embeddings = get_embedding(query)
        top_k_tables = find_top_k_relevant_tables(query_embeddings, MANUAL_TOOL_TABLE_COLLECTION, top_k=3)
        modified_top_k_tables = {}
        for table in top_k_tables:
            current_table_object = {}
            for key in table:
                if key == "table_name":
                    current_table_name = table.get(key)
                else:
                    current_table_object[key] = table.get(key)
            modified_top_k_tables[current_table_name] = current_table_object
        logger.info(f"the top k tables chosen for the query are: {modified_top_k_tables}")
        manual_function_tools_list: List[ChatCompletionToolParam] = []
        for val in MANUAL_FUNCTION_MAP.values():
            manual_function_tools_list.append(
                {
                    "type": "function",
                    "function": {
                        "name": val.name,
                        "description": val.description + f"<table_descriptions>{modified_top_k_tables}</table_descriptions>",
                        "parameters": {
                            "type": "object",
                            "properties": val.args,
                            "required": list(val.args.keys())
                            }
                    }
                }
            )
        return manual_function_tools_list

    async def _get_mcp_tools(self, session_list: ClientSession) -> list[ChatCompletionToolParam]:
        """Retrieves tool definitions from an active MCP session."""
        mcp_tools_list: list[ChatCompletionToolParam] = []
        for session in session_list:
            session_tool_list = await session.list_tools()
            mcp_tools_list += [{
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description or "",
                        "parameters": tool.inputSchema,
                    },
                }
                for tool in session_tool_list.tools if tool.inputSchema.get("properties")]
        return mcp_tools_list

    async def _llm_call(self, messages: list[ChatCompletionMessageParam], tools: list[ChatCompletionToolParam] = None):
        """A dedicated method for making calls to the OpenAI API."""
        params = {
            "model": "gpt-4o", # Using a recommended model
            "max_tokens": 4096,
            "messages": messages,
            "temperature": 0
        }
        if tools:
            params["tools"] = tools
            params["tool_choice"] = "auto"
        
        logger.info(f"Making LLM call with {len(messages)} messages and {len(tools) if tools else 0} tools.")
        try:
            response = await openai_client.chat.completions.create(**params)
            logger.info("Successfully received response from LLM.")
            return response
        except openai.APIStatusError as e:
            logger.error(f"OpenAI API returned an API Status Error: {e.status_code} - {e.response}")
        except openai.APIError as e:
            logger.error(f"OpenAI API Error: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred during the LLM call: {e}")

    def replace_keys(self, prompt, state, replace_keys):
        val = ""
        updated_prompt = prompt
        for key in replace_keys:
            if "." in key:
                key_list = key.split(".")
                if isinstance(state, dict):
                    val = deepcopy(state)
                    for key_part in key_list:
                        if isinstance(val, dict):
                            val = val.get(key_part)
                json_val = json.dumps(val)
                updated_prompt = updated_prompt.replace(key, json_val)
            else:
                val = state.get(key) or val
                json_val = json.dumps(val)
                updated_prompt = updated_prompt.replace(key, json_val)
        return updated_prompt


    async def process_query(self, input_query: str, session_list: List[ClientSession], state: Dict, agent_type: str = "orchestrator") -> str:
        """
        Processes a user query by orchestrating tools and LLM calls.
        """
        # Add the user's query to the chat history
        # self.messages.append({"role": "user", "content": input_query})
        system_prompt_replace_keys = []
        system_prompt = self.replace_keys(self.system_prompt, state, system_prompt_replace_keys)
        if agent_type == "orchestrator":
            user_prompt_replace_keys = ["user_message"]
        if agent_type == "response":
            user_prompt_replace_keys = ["user_message", "orchestrator.results"]
        user_prompt = self.replace_keys(self.user_prompt, state, user_prompt_replace_keys)

        chat_history = state.get(agent_type, {}).get("chat_history", []) or []
        available_tools = []
        if agent_type == "orchestrator":
            tools_from_manual_functions = await self._get_manual_tools(input_query)
            tools_from_mcp_servers = await self._get_mcp_tools(session_list)
            # collect the tools
            tools_set_from_manual_functions = set([obj.get("function", {}).get("name", "") for obj in tools_from_manual_functions])
            tools_set_from_mcp_servers = set([obj.get("function", {}).get("name", "") for obj in tools_from_mcp_servers])
            # response = await session.list_tools()

            available_tools = tools_from_manual_functions + tools_from_mcp_servers

        # 2. Make the initial LLM call to decide on an action
        system_message = {"role": "system", "content": system_prompt}
        current_message = {"role": "user", "content": user_prompt}
        chat_history.append(current_message)
        messages = [system_message] + chat_history
        res = await self._llm_call(messages=messages, tools=available_tools)
        logger.info(f"recieved response from {agent_type}: \n {res}")
        state[agent_type]['chat_history'] = chat_history
        return res, state