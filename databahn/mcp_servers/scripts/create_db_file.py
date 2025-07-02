import pandas as pd
import sqlite3
import os

def convert_csv_to_sqlite(db_name='cybersecurity_mcp.db'):
    """
    Reads all CSV files in the current directory, and converts each
    to a table in a new SQLite database.
    """
    # Find all CSV files in the current directory
    csv_files = [
        "databahn/mcp_servers/data/cloud.csv",
        "databahn/mcp_servers/data/darkweb.csv",
        "databahn/mcp_servers/data/geopolitical.csv",
        "databahn/mcp_servers/data/threat_intel.csv",
        "databahn/mcp_servers/data/vulnerability.csv"
    ]

    if not csv_files:
        print("No CSV files found in the current directory.")
        return

    # Create a connection to the SQLite database
    conn = sqlite3.connect(db_name)

    # Process each CSV file
    for csv_file in csv_files:
        try:
            # Read the CSV file into a pandas DataFrame
            df = pd.read_csv(csv_file)

           # Get the base filename from the full path (e.g., 'cloud.csv')
            base_filename = os.path.basename(csv_file)
            # Use the filename (without .csv) as the table name (e.g., 'cloud')
            table_name = os.path.splitext(base_filename)[0]            # Write the DataFrame to a table in the SQLite database
            df.to_sql(table_name, conn, if_exists='replace', index=False)
            print(f"Successfully converted '{csv_file}' to table '{table_name}' in '{db_name}'.")

        except Exception as e:
            print(f"Error processing '{csv_file}': {e}")

    # Close the database connection
    conn.close()
    print(f"\nDatabase '{db_name}' created successfully with {len(csv_files)} tables.")

if __name__ == '__main__':
    convert_csv_to_sqlite()