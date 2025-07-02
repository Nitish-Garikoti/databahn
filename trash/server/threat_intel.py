import pandas as pd
from mcp.server.fastmcp import FastMCP
from mcp_server.data.threat_intel import get_threat_intel_dataframe

mcp = FastMCP(name="ThreatIntelServer")

conn = sqlite3.connect(':memory:')
# Get the data and load it into the in-memory database
threat_df = get_threat_intel_dataframe()
threat_df.to_sql('threat_intelligence', conn, index=False, if_exists='replace')

@mcp.tools()
def get_general_threat_intelligence(sql_query="SELECT * FROM threat_intelligence;"):
    """
    Queries the general threat intelligence feed using a SQL query.
    
    This tool loads threat data into an in-memory SQLite database and executes
    the provided SQL query against it.

    The database table 'threat_intelligence' contains the following columns:
    - threat_actors (TEXT): Names of known threat actor groups.
    - latest_malware (TEXT): Names of recently active malware families.
    - global_alerts (TEXT): High-level alerts about ongoing security events.
    - related_cve (TEXT): CVE identifiers related to the alerts or malware.

    :param sql_query: A string containing the SQL query to execute. 
                      Defaults to 'SELECT * FROM threat_intelligence;'.
    :return: A pandas DataFrame with the results of the query.
    """

    print(f"Executing SQL query on threat intelligence data: {sql_query}")
    try:
        result_df = pd.read_sql_query(sql_query, conn)
    except Exception as e:
        print(f"Error executing SQL query: {e}")
        return pd.DataFrame() # Return empty dataframe on error
    finally:
        conn.close()
        
    return result_df

@mcp.prompts()
def threat_intel_summary_prompt():
    return "Summarize the current threat landscape based on the available intelligence."

@mcp.resources()
def threat_feed_sources():
    return ["AlienVault", "CrowdStrike", "Internal Feed"]

if __name__ == '__main__':
    mcp.run(port=5000)
