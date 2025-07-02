import json
import csv
import os
from typing import Union, List, Dict, Any

class ReadFile:
    """
    A utility class for reading different types of files.
    """

    @classmethod
    def read_file(cls, file_path: str) -> Union[str, List[List[str]], Dict, None]:
        """
        Reads a file and returns its content based on the file extension.

        This method can handle .txt, .csv, and .json files.

        Args:
            file_path (str): The path to the file to be read.

        Returns:
            - A string for .txt files.
            - A list of lists for .csv files.
            - A dictionary or list for .json files.
            - None if the file is not found or the type is unsupported.
        """
        if not os.path.exists(file_path):
            print(f"Error: File not found at '{file_path}'")
            return None

        _, file_extension = os.path.splitext(file_path)

        try:
            if file_extension == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            
            elif file_extension == '.csv':
                with open(file_path, 'r', encoding='utf-8', newline='') as f:
                    reader = csv.reader(f)
                    return [row for row in reader]
            
            elif file_extension == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            else:
                print(f"Error: Unsupported file type '{file_extension}'. Please use .txt, .csv, or .json.")
                return None
                
        except Exception as e:
            print(f"An error occurred while reading '{file_path}': {e}")
            return None

# --- Example Usage ---
if __name__ == '__main__':
    # Create some dummy files for demonstration
    
    # 1. Create a dummy text file
    with open('sample.txt', 'w') as f:
        f.write("This is a sample text file.\nIt has multiple lines.")
    
    # 2. Create a dummy CSV file
    with open('sample.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['header1', 'header2', 'header3'])
        writer.writerow(['data1', 'data2', 'data3'])
        writer.writerow(['data4', 'data5', 'data6'])
        
    # 3. Create a dummy JSON file
    sample_json = {"name": "John Doe", "age": 30, "isStudent": False}
    with open('sample.json', 'w') as f:
        json.dump(sample_json, f, indent=4)

    # --- Use the ReadFile class method ---
    print("--- Reading sample.txt ---")
    txt_content = ReadFile.read_file('sample.txt')
    if txt_content:
        print(txt_content)
    
    print("\n--- Reading sample.csv ---")
    csv_content = ReadFile.read_file('sample.csv')
    if csv_content:
        for row in csv_content:
            print(row)
            
    print("\n--- Reading sample.json ---")
    json_content = ReadFile.read_file('sample.json')
    if json_content:
        print(json_content)

    # Clean up the dummy files
    os.remove('sample.txt')
    os.remove('sample.csv')
    os.remove('sample.json')
