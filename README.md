# Folder Structure
## Data retrival and response

```
databahn
├── databahn/
│   ├── data/
│   ├── mcp_servers/
│   ├── scripts/
│   ├── tools/
│   ├── utils/
│   ├── __init__.py
│   └── test/
├── .env
├── .gitignore
├── .python-version
├── app.py
├── base.py
├── checklist.md
├── main.py
├── poetry.lock
├── pyproject.toml
├── README.md
├── security_logs.db
└── uv.lock
```

* databahn/: The main source code directory for the application.

* data/: Contains data-related files.

* mcp_servers/: holds logic for MCP servers and data hosted on the mcp servers

* scripts/: contains agent and main

* tools/: Contains various tools used by the application.

* utils/: Holds utility functions.

* test/: Contains tests for the project.

* app.py: The main entry point for the FastAPI application.

* main.py: Contains the primary logic, including calls to the orchestrator, dispatcher, and response handlers.

* checklist.md: A markdown file outlining potential improvements to productionize the codebase.

* pyproject.toml: The project's dependency and configuration file used by Poetry.

This project demonstrates a Python application that can fetch and join information from multiple cybersecurity-themed data sources to answer a user's query. It simulates a real-world scenario where data might be distributed across various tables and systems.


# How to run:

Follow these steps to get the application running locally.

1. Setup Python Environment
First, create and activate a Python virtual environment.
```
# Bash
# Create a virtual environment using Python 3.12
python3.12 -m venv .venv
source .venv/bin/activate
```

2. Install Dependencies
Use Poetry to install the required project dependencies.
```
# Bash
poetry install
```

3. Configure Environment Variables
Create a .env file in the root directory of the project and add your OpenAI API key.
```
# Code snippet
OPENAI_API_KEY="your-secret-key-here"
```

4. Configure Cloudflare MCP Server (Optional)
This project can integrate with a Cloudflare MCP server.
To use the Cloudflare server:
Ensure you have a Cloudflare account.
In a separate terminal, run the following command to authenticate your session:
```
# Bash
npx mcp-remote [https://browser.mcp.cloudflare.com/sse](https://browser.mcp.cloudflare.com/sse)
```
To NOT use the Cloudflare server:
In app.py, find and comment out the lines related to "cloudflare_browser_params", "cf_read", and "cf_write".

5. Start the Application
Finally, start the FastAPI server using Uvicorn.
```
# Bash
poetry run uvicorn app:app --port 8001
```

The application will now be running at http://127.0.0.1:8001. 🚀
