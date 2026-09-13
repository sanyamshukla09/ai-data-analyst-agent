import os
from dotenv import load_dotenv
from openai import OpenAI

# Load variables from .env
load_dotenv()

# Create OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def ask_ai(question, data_summary):
    """
    Send a question and dataset summary to the AI.
    """

    prompt = f"""
You are an expert data analyst.

Here is information about the user's dataset:

{data_summary}

Answer the user's question using the dataset information.

User question:
{question}

Rules:
- Give a clear and simple answer.
- Use numbers when available.
- Explain your reasoning briefly.
- If the information needed is not available, say so.
"""

    response = client.responses.create(
        model="gpt-5-mini",
        input=prompt
    )

    return response.output_text