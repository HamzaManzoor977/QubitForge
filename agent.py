# agent.py

import os
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Debug once (remove later)
print("GROQ KEY LOADED:", os.getenv("GROQ_API_KEY"))

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

def generate(prompt: str) -> str:
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
    )
    return response.choices[0].message.content


def translate_text(text: str, language: str) -> str:
    prompt = f"""
Translate the following text into {language}.
Keep meaning intact and tone professional.

TEXT:
{text}
"""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content
