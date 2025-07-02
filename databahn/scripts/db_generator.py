import sqlite3
import csv
import os

def create_database_and_tables(db_name='security_logs.db', csv_files=None):
    """
    Creates a new SQLite database, creates tables based on CSV file names,
    and populates them with data from the CSV files.

    Args:
        db_name (str): The name of the SQLite database file to create.
        csv_files (list): A list of paths to the CSV files.
    """
    if csv_files is None:
        print("No CSV files provided.")
        return

    # Connect to the SQLite database. This will create the file if it doesn't exist.
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        print(f"Database '{db_name}' created successfully.")

        # Process each CSV file
        for file_path in csv_files:
            try:
                # Derive table name from the CSV filename
                table_name = os.path.splitext(os.path.basename(file_path))[0]

                with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
                    reader = csv.reader(csvfile)
                    
                    # Get header row to define table columns
                    header = next(reader)
                    # Sanitize column names for SQL (replace spaces, etc.)
                    sql_columns = [col.strip().replace(' ', '_').replace('-', '_').replace('.', '_') for col in header]
                    header_col_count = len(sql_columns)

                    # Drop table if it already exists
                    cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
                    
                    # Create table schema dynamically
                    # For simplicity, all columns are treated as TEXT.
                    columns_def = ", ".join([f'"{col}" TEXT' for col in sql_columns])
                    create_table_sql = f"CREATE TABLE {table_name} ({columns_def})"
                    
                    cursor.execute(create_table_sql)
                    print(f"Table '{table_name}' created successfully.")

                    # Insert data into the table
                    placeholders = ", ".join(['?'] * header_col_count)
                    insert_sql = f"INSERT INTO {table_name} VALUES ({placeholders})"
                    
                    # Read the rest of the rows for insertion
                    rows_inserted = 0
                    # Enumerate to get line numbers for better error messages
                    for i, row in enumerate(reader, 2): # Start from line 2
                        # FIX: Skip empty rows
                        if not row:
                            print(f"Warning: Skipping empty line at row {i} in {file_path}")
                            continue

                        # FIX: Check if the row has the correct number of columns
                        if len(row) != header_col_count:
                            print(f"Warning: Skipping malformed row {i} in {file_path}. Expected {header_col_count} columns, but found {len(row)}. Data: {row}")
                            continue
                        
                        # FIX: Added a try-except block for resilience
                        try:
                            cursor.execute(insert_sql, row)
                            rows_inserted += 1
                        except Exception as e:
                            print(f"Error inserting row {i} from {file_path}: {e}. Row data: {row}")

                    print(f"Inserted {rows_inserted} rows into '{table_name}'.")

                conn.commit()

            except FileNotFoundError:
                print(f"Error: The file '{file_path}' was not found.")
            except Exception as e:
                print(f"An error occurred while processing '{file_path}': {e}")
                conn.rollback()

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()
            print(f"Database connection to '{db_name}' closed.")

if __name__ == '__main__':
    # List of CSV files to be loaded into the database.
    # Assumes the script and CSV files are in the same directory.
    data_directory = 'databahn/data/'
    # csv_file_list = [
    #     'data/asset_inventory.csv',
    #     'data/authentication_logs.csv',
    #     'data/dns_logs.csv',
    #     'data/endpoint_security.csv',
    #     'data/firewall_logs.csv',
    #     'data/incident_reports.csv',
    #     'data/network_traffic.csv',
    #     'data/threat_intelligence.csv',
    #     'data/user_activity.csv',
    #     'data/vulnerability_scans.csv',
    #     'data/metadata.csv' # Including the new metadata table
    # ]
    csv_file_list = [
    os.path.join(data_directory, f) 
    for f in os.listdir(data_directory) 
    if f.endswith('.csv')
    ]
    # Create a dummy CSV file if it doesn't exist for demonstration
    for csv_file in csv_file_list:
        if not os.path.exists(csv_file):
            print(f"Warning: '{csv_file}' not found. A dummy file will not be created in this environment.")
            # In a local environment, you might create a dummy file like this:
            # with open(csv_file, 'w', newline='') as f:
            #     writer = csv.writer(f)
            #     if csv_file == 'metadata.csv':
            #         writer.writerow(['table_name', 'column_name', 'data_type', 'description'])
            #     else:
            #         writer.writerow(['dummy_col1', 'dummy_col2'])
            #         writer.writerow(['data1', 'data2'])

    create_database_and_tables(db_name='databahn/data/security_logs.db', csv_files=csv_file_list)
    print("\nScript finished. Check for 'security_logs.db' in the current directory.")

