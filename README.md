# Cybersecurity Data Retriever


cybersecurity_data_retriever/
|-- data/
|   |-- endpoint_security.csv
|   |-- network_traffic.csv
|   |-- vulnerability_scans.csv
|   |-- user_activity.csv
|   |-- authentication_logs.csv
|   |-- threat_intelligence.csv
|   |-- incident_reports.csv
|   |-- firewall_logs.csv
|   |-- dns_logs.csv
|   `-- asset_inventory.csv
|-- mcp_server/
|   |-- mcp_server.py
|   `-- mcp_data.py
|-- main.py
`-- README.md


This project demonstrates a Python application that can fetch and join information from multiple cybersecurity-themed data sources to answer a user's query. It simulates a real-world scenario where data might be distributed across various tables and systems.

## Project Structure

- `data/`: This directory contains 10 sample CSV files, each representing a different cybersecurity data source.
- `mcp_server/`: This directory contains a simple Flask-based "Model Context Protocol" (MCP) server.
    - `mcp_server.py`: The main file for the MCP server.
    - `mcp_data.py`: A helper file that provides data to the MCP server.
- `main.py`: The main application that takes a user query, processes it, and fetches the relevant information.
- `README.md`: This file.

## How to Run the Project

1.  **Install the dependencies:**

    ```bash
    pip install pandas flask
    ```

2.  **Start the MCP Server:**

    Open a terminal and run the following command:

    ```bash
    python mcp_server/mcp_server.py
    ```

    The server will start on `http://127.0.0.1:5000`.

3.  **Run the Main Application:**

    Open another terminal and run the following command:

    ```bash
    python main.py
    ```

    The application will prompt you to enter a query.

## Example Queries

- "Show all critical vulnerabilities."
- "What are the latest threat intelligence feeds?"
- "List all incidents with a 'high' priority."
- "Show all firewall logs from '192.168.1.100'."
- "What are the DNS requests for 'malicious.com'?"

</code></pre>