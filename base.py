import os
from dotenv import load_dotenv
from openai import AsyncOpenAI

# Call the function to load the variables from the .env file
load_dotenv()



OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
CF_SERVER_URL = os.getenv("CF_SERVER_URL")
CF_AUTH_TOKEN = os.getenv("CF_AUTH_TOKEN")
CF_HEADERS = {"Authorization": f"Bearer {CF_AUTH_TOKEN}"}