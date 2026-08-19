from google import genai
from google.genai import types

from bot.config import GEMINI_API_KEY, GEMINI_MODEL

_client = genai.Client(
    api_key=GEMINI_API_KEY,
    http_options=types.HttpOptions(timeout=20000),
)

async def generate_reply(
    history: list[tuple[str, str]],
    sender_name: str,
    user_message: str,
    system_instruction: str,
) -> str:
    lines = [f"{name}: {text}" for name, text in history]
    lines.append(f"{sender_name}: {user_message}")
    transcript = "\n".join(lines)

    response = await _client.aio.models.generate_content(
        model=GEMINI_MODEL,
        contents=[{"role": "user", "parts": [{"text": transcript}]}],
        config=types.GenerateContentConfig(system_instruction=system_instruction),
    )
    text = getattr(response, "text", None)
    if not text:
        raise ValueError("Empty response from Gemini")
    return text
