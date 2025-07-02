from base import openai_client
import sqlite3
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import json
from typing import Union, List
import pandas as pd
import openai

def get_embedding(text, model="text-embedding-3-small"):
   """Generates an embedding for the given text using OpenAI's API."""
   try:
       if not text.strip(): return None
       return openai.embeddings.create(input=[text], model=model).data[0].embedding
   except Exception as e:
       print(f"Error getting embedding: {e}")
       return None

def setup_vector_db(conn: sqlite3.Connection) -> List[dict]:
    """
    Creates a collection of table objects with embeddings from the 'metadata' table.
    This version uses direct SQL queries instead of pandas.

    Args:
        conn: An active sqlite3 connection object.

    Returns:
        A list of dictionaries, where each dictionary represents a table and its embedding.
    """
    print("Setting up vector database from metadata...")
    table_collection = []
    cursor = conn.cursor()

    try:
        # 1. Get a list of unique table names from the metadata
        cursor.execute("SELECT DISTINCT table_name FROM metadata")
        table_names = [row[0] for row in cursor.fetchall()]

        if not table_names:
            print("Warning: 'metadata' table is empty or does not exist.")
            return []

        # 2. For each table, fetch its columns and descriptions
        for table_name in table_names:
            curr_table_object = {"table_name": table_name}
            
            # Fetch all columns for the current table
            cursor.execute("SELECT column_name, column_description FROM metadata WHERE table_name = ?", (table_name,))
            columns_data = cursor.fetchall()
            
            for column_name, description in columns_data:
                curr_table_object[column_name] = description
            
            # 3. Generate and add the embedding for the structured table info
            embedding_text = json.dumps(curr_table_object)
            embedding = get_embedding(embedding_text)
            
            if embedding:
                curr_table_object['embeddings'] = np.array(embedding)
                table_collection.append(curr_table_object)

    except sqlite3.Error as e:
        print(f"Error accessing the database: {e}")
        return []
        
    print(f"Vector database setup complete. {len(table_collection)} tables processed.")
    return table_collection

def find_top_k_relevant_tables(query_embedding: Union[np.ndarray, list[float]], table_collection: list[dict], top_k: int = 3) -> list[dict]:
    """
    Finds the most relevant tables from a collection using cosine similarity.

    This function compares a query embedding against a collection of table
    embeddings and returns the top 'k' table objects that are most
    semantically similar to the query.

    Args:
        query_embedding (Union[np.ndarray, list[float]]): The vector embedding of the user's query,
                                                        as either a list of floats or a numpy array.
        table_collection (list[dict]): A list of dictionaries, where each dict
                                       represents a table and must contain at least
                                       'table_name' (str) and 'embeddings' (np.ndarray) keys.
        top_k (int): The number of top relevant tables to return.

    Returns:
        list[dict]: A list of the top_k most relevant table objects, sorted
                    from most to least relevant, with the 'embeddings' key
                    removed from each. Returns an empty list if inputs are invalid.
    """
    # 1. Handle edge cases where inputs are empty or invalid
    if query_embedding is None or not table_collection:
        return []

    # 2. Ensure query_embedding is a 2D numpy array for compatibility with cosine_similarity.
    # This correctly handles both standard lists and existing numpy arrays.
    try:
        query_embedding_2d = np.array(query_embedding).reshape(1, -1)
    except Exception as e:
        print(f"Error converting query_embedding to a valid numpy array: {e}")
        return []

    # 3. Extract table embeddings from the collection
    try:
        table_embeddings = np.array([obj['embeddings'] for obj in table_collection])
    except (KeyError, TypeError):
        print("Error: table_collection must be a list of dicts with 'embeddings' keys.")
        return []

    # 4. Calculate cosine similarity between the single query and all table embeddings.
    # The result is a 2D array, so we select the first (and only) row.
    similarities = cosine_similarity(query_embedding_2d, table_embeddings)[0]

    # 5. Get the indices of the 'top_k' highest similarity scores.
    # np.argsort sorts in ascending order, so we use slicing to reverse it.
    top_k_indices = np.argsort(similarities)[-top_k:][::-1]

    # 6. Retrieve the full objects and remove the 'embeddings' key for the final result.
    # This creates a new list of new dictionaries, preserving the original collection.
    relevant_objects = [
        {key: value for key, value in table_collection[i].items() if key != 'embeddings'}
        for i in top_k_indices
    ]

    return relevant_objects


TOOL_DB_FILE = 'databahn/data/security_logs.db'
conn = sqlite3.connect(TOOL_DB_FILE)
MANUAL_TOOL_TABLE_COLLECTION = setup_vector_db(conn)
conn.close()


# --- Example Usage ---
if __name__ == '__main__':
    # Mock data for demonstration, simulating OpenAI's output format
    mock_query_embedding_list = [0.8, 0.2, 0.6]

    mock_table_collection = [
        {'table_name': 'firewall_logs', 'embeddings': np.array([0.8, 0.1, 0.3]), 'source': 'syslog'},
        {'table_name': 'asset_inventory', 'embeddings': np.array([0.2, 0.8, 0.1]), 'source': 'cmdb'}, # Most similar
        {'table_name': 'dns_logs', 'embeddings': np.array([0.9, 0.2, 0.1]), 'source': 'syslog'},
        {'table_name': 'vulnerability_scans', 'embeddings': np.array([0.3, 0.3, 0.9]), 'source': 'scanner'},
        {'table_name': 'user_activity', 'embeddings': np.array([0.1, 0.7, 0.4]), 'source': 'endpoint'} # Second most similar
    ]

    # Find the top 3 relevant tables using the list
    top_table_objects = find_top_k_relevant_tables(mock_query_embedding_list, mock_table_collection, top_k=3)

    print("Query Embedding (as list):", mock_query_embedding_list)
    print("\nTop 3 relevant table objects (embeddings removed):")
    # Pretty-print the list of dictionaries
    print(json.dumps(top_table_objects, indent=4))
    # Expected output: A list containing the 'asset_inventory', 'user_activity', and 'firewall_logs' objects.



