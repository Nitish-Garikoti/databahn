from langchain.tools import tool
from databahn.utils.data_objects import Result, ContentObject
import sqlite3


# --- Configuration ---
DB_FILE = 'databahn/data/security_logs.db'
conn = sqlite3.connect(DB_FILE)

@tool
async def lookup_cybser_security_data(sql_query: str) -> str:
    """
    Execute SQL queries safely
    Here is the description of tables handled by this tool.
    You can join tables in your sql_query if required to retrieve the required information
    for regions if countries are provided then do a fuzzy search on continent of the country.
    input_args: 
      sql_query: sql query that can join tables to extract the data required to answer the input_message
    """
    print(f"The incoming SQL query: {sql_query}")
    try:
        result = conn.execute(sql_query).fetchall()
        conn.commit()
        content = "\n".join(str(row) for row in result)
        return Result(content=[ContentObject(text=content)])
    except Exception as e:
        raise ValueError



MANUAL_FUNCTION_MAP = {
 "lookup_cybser_security_data": lookup_cybser_security_data
}