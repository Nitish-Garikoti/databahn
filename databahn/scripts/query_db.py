import sqlite3
import os
import pandas as pd

def query_vulnerabilities(db_name='security_logs.db'):
    """
    Connects to the specified SQLite database and runs a query to find
    all critical vulnerabilities that are still pending.

    Args:
        db_name (str): The name of the SQLite database file to query.
    """
    try:
        conn = sqlite3.connect(db_name)
        print("\n--- Running Example Query ---")
        print("Query: Find all 'Critical' severity vulnerabilities with a 'Pending' status.")

        # The SQL query to select specific vulnerabilities
        # We also join with asset_inventory to get the asset_name for better context.
        query = """
        SELECT
            vs.scan_id,
            vs.asset_id,
            ai.asset_name,
            vs.vulnerability,
            vs.cvss_score,
            vs.status
        FROM
            vulnerability_scans vs
        JOIN
            asset_inventory ai ON vs.asset_id = ai.asset_id
        WHERE
            vs.severity = 'Critical' AND vs.status = 'Pending'
        """

        # Using pandas to execute the query and display the results in a clean table
        df = pd.read_sql_query(query, conn)

        if df.empty:
            print("No critical, pending vulnerabilities found.")
        else:
            print("Query Results:")
            print(df.to_string())

    except sqlite3.Error as e:
        print(f"Database query error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during query: {e}")
    finally:
        if conn:
            conn.close()
            print("\nDatabase connection for querying closed.")



if __name__ == '__main__':    
    # --- Step 2: Run the example query ---
    query_vulnerabilities()

    print("\nScript finished.")
