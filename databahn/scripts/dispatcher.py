

from databahn.tools.tools import MANUAL_FUNCTION_MAP
import json
from typing import cast, Any, Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Dispatcher():
    async def _handle_browser_tool(self, session: Any, tool_name: str, tool_args: Dict[str, Any], tools_dict: Dict[str, Any]) -> Any:
        """
        Handles the specific logic for browser tools, including setting the active account.
        """
        logger.info(f"Dispatching browser tool: {tool_name}")
        result = await session.call_tool(tool_name, cast(dict, tool_args))

        # Check if the result contains the specific error message.
        result_content = getattr(result.content[0], "text", "") if result and result.content else ""
        if "No currently active accountId" in result_content:
            logger.info("Active account not set. Attempting automatic setup...")
            # The session for browser tools is the one we already have.
            browser_session = session
            # 1. List accounts
            accounts_result = await browser_session.call_tool("accounts_list", {})
            accounts_content = getattr(accounts_result.content[0], "text", "") if accounts_result and accounts_result.content else ""
            try:
                # The result is often a JSON string in a list, parse it.
                json_accounts_data = json.loads(accounts_content)
                accounts_data = json_accounts_data.get('accounts') or []
                if accounts_data and len(accounts_data) > 0:
                    # 2. Get the first account ID
                    account_id = accounts_data[0].get("id")
                    if account_id:
                        logger.info(f"Found account ID: {account_id}. Setting it as active.")
                        # 3. Set the active account
                        await browser_session.call_tool("set_active_account", {"activeAccountIdParam": account_id})
                        
                        # 4. Retry the original tool call
                        logger.info(f"Retrying original tool call: {tool_name}")
                        result = await session.call_tool(tool_name, cast(dict, tool_args))
                    else:
                        logger.error("Could not find 'id' in account data.")
                else:
                    logger.error("accounts_list returned no accounts.")
            except (json.JSONDecodeError, IndexError, KeyError) as e:
                logger.error(f"Failed to parse accounts list or find account ID: {e}")
        
        return result

    async def dispatcher_invoke(self, tool_calls, session_list):
        """
        method to dispatch the tool calls and get the results
        """
        tool_results  = []
        tools_dict_from_mcp_servers = {tool.name: session for session in session_list
                                          for tool in (await session.list_tools()).tools}

        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            # Arguments from OpenAI come as a JSON string
            tool_args_str = tool_call.function.arguments
            try:
                tool_args = json.loads(tool_args_str)
            except json.JSONDecodeError:
                print(f"Error: Invalid JSON in tool arguments: {tool_args_str}")
                continue
            try:
                if tool_name in MANUAL_FUNCTION_MAP: 
                    logger.info(f"Dispatching the tool: {tool_name} in manual tools")
                    result = await MANUAL_FUNCTION_MAP[tool_name].ainvoke(tool_args)
                elif tools_dict_from_mcp_servers.get(tool_name):
                    session = tools_dict_from_mcp_servers[tool_name]
                    # --- MODIFIED: Check if the tool belongs to the browser server ---
                    browser_session = tools_dict_from_mcp_servers.get("accounts_list")
                    if browser_session and session is browser_session:
                        result = await self._handle_browser_tool(session, tool_name, tool_args, tools_dict_from_mcp_servers)
                    else:
                        logger.info(f"Dispatching tool: {tool_name} under a non-browser mcp server")
                        result = await session.call_tool(tool_name, cast(dict, tool_args))
                    # session = tools_dict_from_mcp_servers.get(tool_name)
                    # logger.info(f"Dispatching the tool the tool: {tool_name} under mcp server")
                    # # Execute tool call (this part remains the same)
                    # result = await session.call_tool(tool_name, cast(dict, tool_args))
                else: 
                    result = ""
            except Exception as e:
                result = ""
        
            logger.info(f"dispatched tool result:{result}")
            if result and isinstance(result.content, list) and result.content:
                # Add the tool result to our list for the next API call
                tool_results.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": getattr(result.content[0], "text", ""),
                    }
                )
            else:
                # Add the tool result to our list for the next API call
                tool_results.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": "",
                    }
                )
        logger.info(f"the tool_results are: {str(tool_results)[:100]}")
        return tool_results
