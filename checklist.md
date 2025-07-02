logging
UI with html chat
state in redis
messages and agent class
chat_history for orchestrator
chat_history for response



using config to initialize
saving the logs - mongodb
cost/metrics using langfuse
prompt engineering:
    1. I have added JSON schema of tables RAG on manual tools  but this is not perfect.  I haven't added the RAG for mcp tool doc strings but that possible too using resources. Even in manual tools RAG its better if we do html tagging extraction of tables and then RAG and put back the appropriate tables. I currently used a table that has all other table info - This will be problematic if we have more tools with different tables.
    2. Add RAG on MCP tools and each tool MCP tables.
    3. Add few shot examples
    4. Dynamic system prompting - Currently static prompt and I can add this dynamically - tables and also few shot examples.
Fine tuning(orchestrator)
make jinja resposne and render the data to look it more appealing on UI
latencies in debug_obj
multiple mcp servers or module based agentic approach
streaming
Limit the number of responses returned by the SQL query(I did it default at 10) but this has to be product dependent.
benchmark and evaluation
follow up questions


1. Public facing MCP servers for cyber security data.(Implemented it but not a tool for sql search on db.)
2. Websearch (Implemented it)
