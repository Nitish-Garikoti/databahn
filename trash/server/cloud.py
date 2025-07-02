<pre><code class="language-python">import pandas as pd
import sqlite3
# This import assumes the mcp library is installed.
# from mcp.server.fastmcp import FastMCP 
from data.cloud_data import get_cloud_dataframe

conn = sqlite3.connect(':memory:')

# Get the data and load it into the in-memory database
df = get_cloud_dataframe()
df.to_sql('cloud_security', conn, index=False, if_exists='replace')


# --- Server Definition ---

mcp = FastMCP(name="CloudSecurityServer")

@mcp.tools()
def get_cloud_security_posture(sql_query="SELECT * FROM cloud_security;"):
    """
    Queries the cloud security posture feed using a SQL query.
    
    This tool loads cloud security data into an in-memory SQLite database 
    and executes the provided SQL query against it.

    The database table 'cloud_security' contains the following columns:
    - cloud_provider (TEXT): The name of the cloud service provider (e.g., AWS, Azure).
    - misconfiguration (TEXT): A description of the security misconfiguration.
    - threat_vector (TEXT): The potential threat resulting from the misconfiguration.
    - recommendation (TEXT): The recommended action to remediate the issue.

    :param sql_query: A string containing the SQL query to execute. 
                      Defaults to 'SELECT * FROM cloud_security;'.
    :return: A pandas DataFrame with the results of the query.
    """
    print(f"Executing SQL query on cloud security data: {sql_query}")
    try:
        result_df = pd.read_sql_query(sql_query, conn)
    except Exception as e:
        print(f"Error executing SQL query: {e}")
        return pd.DataFrame() # Return empty dataframe on error
    finally:
        conn.close()
        
    return result_df

@mcp.prompts()
def cloud_misconfiguration_remediation_prompt():
    return "Provide a step-by-step guide to remediate the specified cloud misconfiguration."

@mcp.resources()
def cloud_providers():
    return ["AWS", "Azure", "GCP"]

if __name__ == '__main__':
    mcp.run(port=5004)