from contextlib import asynccontextmanager
from typing import Dict, Any, Optional
from databahn.scripts.main import Chat
from fastapi import FastAPI, HTTPException
from mcp import ClientSession, StdioServerParameters
from copy import deepcopy
from pydantic import BaseModel
import logging
from mcp.client.stdio import stdio_client
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app_state: Dict[str, Any] = {}

# npx mcp-remote https://browser.mcp.cloudflare.com/sse
# create server
cyber_sec_server_params=StdioServerParameters(
    command="python",
    args=["databahn/mcp_servers/scripts/cyber_sec_server.py"]
    )

internet_search_server_params = StdioServerParameters(
    command="python",
    args=["databahn/mcp_servers/scripts/internet_search_server.py"]
)

cloudflare_browser_params = StdioServerParameters(
    command="npx",
    args=["mcp-remote", "https://browser.mcp.cloudflare.com/sse"]
)

redis_object = {
        "user_message": "",
        "orchestrator": {"chat_history": []},
        "response": {"chat_history": []}
    }

# Define the request model for the API endpoint, now with thread_id
class QueryRequest(BaseModel):
    query: str
    thread_id: str # A unique ID for each conversation thread

# Define the response model
class QueryResponse(BaseModel):
    response: str
    state: Optional[Dict]

@asynccontextmanager
async def lifespan(app: FastAPI):
    # This code runs on startup
    logger.info("Application startup...")
    logger.info("Initializing Chat instance...")
    app_state["chat_instance"] = Chat()
    
    logger.info("Connecting to MCP server...")
    # The stdio_client context manager will handle the read/write streams
    async with stdio_client(cyber_sec_server_params) as (cs_read, cs_write), \
               stdio_client(internet_search_server_params) as (is_read, is_write), \
               stdio_client(cloudflare_browser_params) as (cf_read, cf_write):
        
        # Create client sessions for both servers
        async with ClientSession(cs_read, cs_write) as cs_session, \
                   ClientSession(is_read, is_write) as is_session, \
                   ClientSession(cf_read, cf_write) as cf_session:
            
            # Initialize both sessions concurrently
            await asyncio.gather(
                cs_session.initialize(),
                is_session.initialize(),
                cf_session.initialize()
            )
            
            # Store named sessions in the app state dictionary
            # app_state["mcp_sessions"]["cyber_security"] = cs_session
            # app_state["mcp_sessions"]["internet_search"] = is_session
            app_state['mcp_sessions'] = [cs_session, is_session, cf_session]
            
            logger.info("All MCP sessions initialized and ready.")
            yield

    # This code runs on shutdown
    logger.info("Application shutdown...")
    # The context managers for ClientSession and stdio_client will handle cleanup automatically


# Create the FastAPI app with the lifespan context manager
app = FastAPI(lifespan=lifespan)


@app.post("/query", response_model=QueryResponse)
async def handle_query(request: QueryRequest):
    """
    Accepts a user query, processes it through the Chat class, 
    and returns the final response.
    """
    if "mcp_sessions" not in app_state or "chat_instance" not in app_state:
        raise HTTPException(status_code=503, detail="MCP session not ready. Please try again shortly.")

    session_list = app_state["mcp_sessions"]
    chat = app_state["chat_instance"]

    # read state from redis using user_id in cache_id
    # Initialize a new, clean state for each request to ensure statelessness
    global redis_object
    state = deepcopy(redis_object)
    state['user_message'] = request.query
    # limit chat history to last 5 messages
    state["orchestrator"]["chat_history"] = state["orchestrator"]["chat_history"][-5:]
    state["response"]["chat_history"] = state["response"]["chat_history"][-5:]
    try:
        # Process the query using the shared session and a fresh state
        response_content, state = await chat.process_query(request.query, session_list, state)
        redis_object = deepcopy(state)
        # write state to redis using the cache_id created above(based on user_id)
        logger.info(f"the response content we are returning:{response_content}")
        return QueryResponse(response=response_content, state=state)
    except Exception as e:
        logger.error(f"An error occurred while processing query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred.")