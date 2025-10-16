import os
from dotenv import load_dotenv
from groq import Groq

# Load variables from .env file
load_dotenv(dotenv_path="./.env")

# Get API key from environment variables
api_key = os.environ.get("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY is missing. Check your .env file.")

# Initialize Groq client
client = Groq(api_key=api_key)

chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "are u good at science",
        },
        {
            "role": "system",
            "content": "You are a e-commerce competitor analyst",
        }
    ],
    model="llama-3.3-70b-versatile",
)

print(chat_completion.choices[0].message.content)