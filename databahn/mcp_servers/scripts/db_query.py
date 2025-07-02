import sqlite3

def inspect_database(db_path):
    """
    Connects to an SQLite database and prints all tables and their columns.

    Args:
        db_path (str): The path to the SQLite database file.
    """
    try:
        # Establish a connection to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        print(f"Successfully connected to {db_path}\n")

        # Get a list of all tables in the database
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        if not tables:
            print("No tables found in this database.")
            return

        print("--- Database Schema ---")
        # Iterate over the tables
        for table_name_tuple in tables:
            table_name = table_name_tuple[0]
            print(f"\nTable: {table_name}")

            # Get the column information for the current table
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()

            # Print each column's name (the second item in the tuple)
            for column in columns:
                print(f"  - {column[1]}")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Ensure the connection is closed
        if conn:
            conn.close()
            print("\n-----------------------\nConnection closed.")

if __name__ == '__main__':
    # The path to your database file
    database_file = 'databahn/mcp_servers/data/cybersecurity_mcp.db'
    inspect_database(database_file)