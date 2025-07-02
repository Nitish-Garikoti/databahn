import pandas as pd
import sqlite3
# from mcp.server.fastmcp import FastMCP
from data.darkweb_data import get_darkweb_dataframe

conn = sqlite3.connect(':memory:')
df = get_darkweb_dataframe()
df.to_sql('darkweb_monitoring', conn, index=False, if_exists='replace')

# --- Server Definition ---
mcp = FastMCP(name="DarkWebMonitoringServer")

@mcp.tools()
def get_dark_web_data(sql_query="SELECT * FROM darkweb_monitoring;"):
    """
    Queries the dark web monitoring feed using a SQL query.

    The database table 'darkweb_monitoring' contains the following columns:
    - forum (TEXT): The name of the dark web forum or marketplace.
    - post_type (TEXT): The type of illicit good or data being offered.
    - summary (TEXT): A summary of the post or offering.
    - confidence (TEXT): The confidence level of the intelligence (e.g., High, Medium).

    :param sql_query: A string containing the SQL query to execute.
    :return: A pandas DataFrame with the results of the query.
    """
    print(f"Executing SQL query on dark web data: {sql_query}")
    try:
        result_df = pd.read_sql_query(sql_query, conn)
    except Exception as e:
        print(f"Error executing SQL query: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
        
    return result_df

@mcp.prompts()
def dark_web_alert_prompt():
    return "Alert on any new high-confidence credential leaks from the dark web."

@mcp.resources()
def dark_web_forums():
    return ["BreachForums", "XSS.is", "Exploit.in"]

if __name__ == '__main__':
    mcp.run(port=5003)