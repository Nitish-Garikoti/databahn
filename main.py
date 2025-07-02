import os
import re
import pandas as pd
import sqlite3
import openai
import numpy as np
import faiss
import asyncio
from functools import partial
from agents import Agent, Runner, function_tool
from agents.mcp import MCPServerStdio

# --- Configuration ---
DB_FILE = 'security_logs.db'
# Make sure to set your OpenAI API key as an environment variable
# export OPENAI_API_KEY='your_key_here'
openai.api_key = os.getenv("OPENAI_API_KEY")

# --- Database and RAG Functions (Adapted from original script) ---

def get_embedding(text, model="text-embedding-3-small"):
   """Generates an embedding for the given text using OpenAI's API."""
   if not openai.api_key: return None
   try:
       if not text.strip(): return None
       return openai.embeddings.create(input=[text], model=model).data[0].embedding
   except Exception as e:
       print(f"Error getting embedding: {e}")
       return None

def setup_vector_db(conn):
    """Creates a FAISS vector database from the 'metadata' table."""
    print("Setting up vector database from metadata...")
    try:
        metadata_df = pd.read_sql_query("SELECT * FROM metadata", conn)
    except pd.io.sql.DatabaseError:
        print("Error: 'metadata' table not found. Vector DB setup failed.")
        return None, None

    table_embeddings, index_to_table_map = [], {}
    for i, (table_name, group) in enumerate(metadata_df.groupby('table_name')):
        cols = [f"{row['column_name']} ({row['description']})" for _, row in group.iterrows()]
        schema_info = f"Table name: {table_name}. Columns: {', '.join(cols)}."
        embedding = get_embedding(schema_info)
        if embedding:
            table_embeddings.append(embedding)
            index_to_table_map[i] = table_name

    if not table_embeddings: return None, None
    dimension = len(table_embeddings[0])
    faiss_index = faiss.IndexFlatL2(dimension)
    faiss_index.add(np.array(table_embeddings, dtype=np.float32))
    print(f"Vector DB setup complete with {faiss_index.ntotal} embeddings.")
    return faiss_index, index_to_table_map

def find_top_k_relevant_tables(query_embedding, faiss_index, index_to_table_map, top_k=3):
    """Finds the most relevant tables using vector similarity search."""
    if query_embedding is None or faiss_index.ntotal == 0: return []
    distances, indices = faiss_index.search(np.array([query_embedding], dtype=np.float32), min(top_k, faiss_index.ntotal))
    return [index_to_table_map[i] for i in indices[0]]

async def generate_sql_for_single_table(user_query, table_name, conn):
    """Generates a SQL query for a single table by calling an LLM."""
    print(f"Generating SQL for table: {table_name}...")
    prompt = "You are an expert SQLite query writer. Write a single, executable SQLite query to answer the user's question based on the provided table schema. Only output the raw SQL query.\n\n"
    try:
        schema_df = pd.read_sql_query(f"SELECT column_name, data_type, description FROM metadata WHERE table_name = '{table_name}'", conn)
        columns = [f"{row['column_name']} (Type: {row['data_type']}, Description: {row['description']})" for _, row in schema_df.iterrows()]
        prompt += f"Schema for table '{table_name}': {', '.join(columns)}\n\n"
    except Exception as e:
        print(f"Warning: Could not fetch rich schema from metadata for {table_name}: {e}")
        return None
        
    prompt += f"User's Question: '{user_query}'\n\nSQL Query:"

    if not openai.api_key: return None
    try:
        response = await asyncio.to_thread(
            openai.chat.completions.create,
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are an expert SQLite query writer."},
                {"role": "user", "content": prompt}
            ]
        )
        sql_query = response.choices[0].message.content.strip().replace("```sql", "").replace("```", "")
        print(f"Generated SQL: {sql_query}")
        return sql_query
    except Exception as e:
        print(f"Error generating SQL for {table_name}: {e}")
        return None

async def generate_llm_response(results_list, query):
    """Generates a final natural language response based on the data."""
    print("\nSynthesizing final answer...")
    if not openai.api_key: return "OpenAI API key not set."

    context = f"You are a helpful cybersecurity analyst. Based on the following information, answer the user's query.\n\nUser Query: \"{query}\"\n\n"
    if not results_list: return "I was unable to find any information related to your query."

    for result in results_list:
        context += f"--- Data from tool: {result['source_tool']} ---\n{result['data']}\n\n"
    
    context += "Provide a concise, natural language answer based on the data above. If the data is insufficient, state that."

    try:
         response = await asyncio.to_thread(
            openai.chat.completions.create,
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful cybersecurity analyst summarizing data."},
                {"role": "user", "content": context}
            ]
        )
         return response.choices[0].message.content
    except Exception as e:
        return f"An error occurred during final response generation: {e}"

# --- Agent Tools ---

@function_tool
async def query_threat_intel_server(query: str) -> str:
    """
    Queries the threat intelligence server for information on an indicator.
    This is a mock function for demonstration.
    """
    # Simple regex to find an IP address
    ip_match = re.search(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', query)
    if ip_match:
        indicator = ip_match.group(0)
        print(f"Querying mock threat intel server for IP: {indicator}")
        mock_responses = {
            "104.28.14.12": "IP: 104.28.14.12. Threat Type: Malware C2. Associated with TrickBot malware family. Last seen: 2023-10-26.",
            "198.51.100.55": "IP: 198.51.100.55. Threat Type: Botnet. Known command and control server for the Mirai botnet. Last seen: 2023-10-26."
        }
        return mock_responses.get(indicator, f"No threat intelligence found for IP: {indicator}.")
    return "No recognized threat indicator (e.g., IP address) found in the query."


@function_tool
async def query_vulnerability_intel_server(query: str) -> str:
    """
    Queries the vulnerability intelligence server for details on a specific CVE.
    This is a mock function for demonstration.
    """
    cve_match = re.search(r'(CVE-\d{4}-\d{4,7})', query, re.IGNORECASE)
    if not cve_match:
        return "No CVE identifier found in the query."
    cve_id = cve_match.group(1).upper()
    print(f"Querying mock vulnerability server for: {cve_id}")
    # Mock data
    mock_responses = {
        "CVE-2021-44228": "Vulnerability: Apache Log4j RCE (Log4Shell). CVSS Score: 10.0. Description: A remote code execution vulnerability in Apache Log4j 2. Affects products using Log4j versions 2.0 to 2.14.1.",
        "CVE-2017-5638": "Vulnerability: Apache Struts RCE. CVSS Score: 10.0. Description: A remote code execution vulnerability in the Jakarta Multipart parser. Affects Apache Struts 2.3.5 - 2.3.31 and 2.5 - 2.5.10."
    }
    return mock_responses.get(cve_id, f"No information found for {cve_id}.")

@function_tool
async def query_security_database(query: str, conn, vector_db_index, table_map) -> str:
    """
    Answers a query by performing a RAG process against the local security database.
    """
    query_embedding = get_embedding(query)
    relevant_tables = find_top_k_relevant_tables(query_embedding, vector_db_index, table_map)

    if not relevant_tables:
        return "Could not identify any relevant data tables for the query."

    all_results_str = ""
    for table in relevant_tables:
        sql_query = await generate_sql_for_single_table(query, table, conn)
        if sql_query:
            try:
                results_df = pd.read_sql_query(sql_query, conn)
                if not results_df.empty:
                    all_results_str += f"Results from table '{table}':\n{results_df.to_string(index=False)}\n\n"
            except Exception as e:
                print(f"Error executing SQL on {table}: {e}")

    return all_results_str if all_results_str else "Executed queries on relevant tables but found no matching data."


# --- Main Application Logic ---
async def main():
    """Main asynchronous function to run the agent."""
    if not openai.api_key:
        print("CRITICAL: OPENAI_API_KEY environment variable not set. This application requires it to function.")
        return

    db_conn = None
    try:
        if not os.path.exists(DB_FILE):
            print(f"CRITICAL: Database file '{DB_FILE}' not found.")
            return
        db_conn = sqlite3.connect(DB_FILE)
        
        vector_db_index, table_map = setup_vector_db(db_conn)
        if not vector_db_index:
            print("Exiting due to failure in vector database setup.")
            return

        # Bind the necessary arguments to the database query tool
        db_tool = partial(query_security_database, conn=db_conn, vector_db_index=vector_db_index, table_map=table_map)
        # Decorate the partial object so the framework recognizes it
        db_tool = function_tool(db_tool)
        db_tool.__name__ = 'query_security_database' # Preserve the name

        # Set up the MCP servers with their tools
        mcp_vuln_server = MCPServer(
            name="Vulnerability Intel Server",
            description="Provides detailed information about specific software vulnerabilities (CVEs).",
            tool_function=query_vulnerability_intel_server
        )
        mcp_threat_intel_server = MCPServer(
            name="Threat Intel Server",
            description="Provides intelligence on threat indicators like malicious IP addresses or domains.",
            tool_function=query_threat_intel_server
        )

        async with mcp_vuln_server, mcp_threat_intel_server:
            agent = Agent(
                name="Cybersecurity Analyst",
                instructions="You are an expert cybersecurity analyst. First, determine if the user is asking about a specific CVE or IP address. If so, use the appropriate server. Otherwise, use the security database tool to answer questions about security logs, assets, and incidents.",
                model='gpt-4-turbo',
                tools=[db_tool],
                mcp_servers=[mcp_vuln_server, mcp_threat_intel_server],
            )
            
            prompt = "What critical vulnerabilities are pending on our servers?"
            # prompt = "Give me details on CVE-2021-44228." # <-- Alternative prompt to test the other tool
            # prompt = "Tell me about the IP address 104.28.14.12" # <-- New prompt to test threat intel

            result = await Runner.run(agent, prompt)
            print("\n--- Final Answer ---")
            print(result.get("final_output", "No output generated."))

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if db_conn:
            db_conn.close()
            print("\nDatabase connection closed.")

if __name__ == "__main__":
    asyncio.run(main())
