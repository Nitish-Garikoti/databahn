import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv

from agents import Agent, Runner, function_tool
from agents.mcp import MCPServerStdio

# Call the function to load the variables from the .env file
load_dotenv()

# --- 1. Define a Tool ---
# This is a regular Python function decorated with @function_tool.
# The agent can decide to call this function to get information.
@function_tool
async def get_time() -> str:
    """Returns the current date and time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# --- 2. Define an MCP Server ---
# This server gives the agent the ability to perform more complex actions,
# like fetching content from a URL.
mcp_vuln = MCPServerStdio(params={
    "command": "python",
    "args": ["databahn/mcp_servers/server/vulnerability.py"]
}, client_session_timeout_seconds=30.0)

# --- 3. Make the script asynchronous to handle the MCP server ---
async def main():
    # The "async with" block starts the MCP server and ensures it's shut down properly.
    async with mcp_vuln:
        # --- 4. Update the Agent with tools and mcp_servers ---
        agent = Agent(
            name="Assistant",
            instructions="You are a helpful assistant. Use your tools to answer requests.",
            model='gpt-4.1',
            # Add the function tool to the agent
            tools=[get_time],
            # Add the MCP server to the agent
            mcp_servers=[mcp_vuln],
        )

        # --- 5. Update the prompt to use the new capabilities ---
        prompt = (
            "fetch me the cves and the products they are affecting"
        )

        print(f"the prompt is: {prompt}")
        # Use the asynchronous runner
        result = await Runner.run(agent, prompt)
        print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())