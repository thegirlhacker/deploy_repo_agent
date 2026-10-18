
import os
from google import genai


def ask(prompt):
    """Send a prompt to Gemini and return its text response."""

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY environment variable is not set")

    model = os.getenv("LLM_MODEL", "gemini-2.5-flash")

    client = genai.Client(api_key=api_key)

    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
        )
    except Exception as e:
        raise RuntimeError(f"Gemini API request failed: {e}") from e

    if not response.text:
        raise RuntimeError("Gemini returned an empty response")

    return response.text.strip()
