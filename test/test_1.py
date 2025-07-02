from langchain.tools import tool
from typing import List

@tool
def multiply(a: int, b: int, apple: List) -> int:
    """Multiply two numbers."""
    return a * b

print("Tool name:", multiply.name)  # Prints the name of the tool.
print("Tool description:", multiply.description)  # Prints the tool's docstring as the description.
print("Tool input arguments (schema):", multiply.args) 


test_object = [
            {
                "type": "function",
                "function": {
                    "name": multiply.name,
                    "description": multiply.description,
                    "parameters": {
                        "type": "object",
                        "properties": multiply.args,
                        "required": list(multiply.args.keys())
                        }
                }
            }
        ]
print("the object is:", test_object)
