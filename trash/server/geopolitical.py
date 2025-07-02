import pandas as pd
import sqlite3
# from mcp.server.fastmcp import FastMCP
from data.geopolitical_data import get_geopolitical_dataframe

conn = sqlite3.connect(':memory:')
df = get_geopolitical_dataframe()
df.to_sql('geopolitical_threats', conn, index=False, if_exists='replace')

# --- Server Definition ---
mcp = FastMCP(name="GeopoliticalThreatServer")

@mcp.tools()
def get_geopolitical_threats(sql_query="SELECT * FROM geopolitical_threats;"):
    """
    Queries the geopolitical threat feed using a SQL query.

    The database table 'geopolitical_threats' contains the following columns:
    - region (TEXT): The geopolitical region of interest.
    - threat_group (TEXT): The name of the threat actor group.
    - targeted_sector (TEXT): The primary industries or sectors targeted.
    - activity_summary (TEXT): A summary of the observed malicious activity.

    :param sql_query: A string containing the SQL query to execute.
    :return: A pandas DataFrame with the results of the query.
    """
    print(f"Executing SQL query on geopolitical data: {sql_query}")
    try:
        result_df = pd.read_sql_query(sql_query, conn)
    except Exception as e:
        print(f"Error executing SQL query: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
        
    return result_df

@mcp.prompts()
def geopolitical_briefing_prompt():
    return "Provide a geopolitical threat briefing for the specified region."

@mcp.resources()
def geopolitical_analysis_sources():
    return ["Mandiant Reports", "Recorded Future"]

if __name__ == '__main__':
    mcp.run(port=5002)