from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


async def generate_gemini_response(message: str, persona: str = None):
    system_prompt = """You are Aether AI, a concise and clear assistant.
            Use Markdown (headers, lists, tables).
            - For Flowcharts/Diagrams: Use Mermaid syntax inside '```mermaid' code blocks. Ensure diagrams are clear and expansive.
            - For Flashcards: Return them as a JSON block inside '```flashcards' containing an array of objects with 'front' and 'back' fields. Use detailed content.
            - For Image Generation: If asked for an image, translate the user's request into a highly descriptive English prompt (max 50 words). Return ONLY the markdown image tag: ![Image Description](https://pollinations.ai/p/ENCODED_PROMPT?width=1024&height=1024&seed=RANDOM_NUMBER&model=flux). IMPORTANT: Replace ENCODED_PROMPT with the actual prompt where EVERY non-alphanumeric character (spaces, commas, symbols) is URL encoded (e.g., spaces to %20, commas to %2C).
            Always focus on high-quality structured output and premium presentation."""

    if persona:
        system_prompt += f"\n\nCURRENT PERSONA: {persona}\nAdopt this personality, tone, and knowledge base strictly. Respond in the style of this individual while maintaining the structural requirements above."

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=message,
        config={
            "system_instruction": system_prompt,
            "max_output_tokens": 2000,
        }
    )

    return response.text