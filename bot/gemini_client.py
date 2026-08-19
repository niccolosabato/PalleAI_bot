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


async def generate_psychoanalysis(
    target_name: str,
    messages: list[str],
    system_instruction: str,
) -> str:
    quotes = "\n".join(f"- {text}" for text in messages)
    prompt = (
        f"Fai una finta psicoanalisi scherzosa di {target_name}, restando fedele al tuo personaggio. "
        f"Basati sui suoi messaggi qui sotto per inventare un profilo psicologico assurdo e specifico su di lui. "
        f"Scrivi un paragrafo di 3-5 frasi, niente elenchi puntati.\n\n"
        f"Messaggi di {target_name}:\n{quotes}"
    )

    response = await _client.aio.models.generate_content(
        model=GEMINI_MODEL,
        contents=[{"role": "user", "parts": [{"text": prompt}]}],
        config=types.GenerateContentConfig(system_instruction=system_instruction),
    )
    text = getattr(response, "text", None)
    if not text:
        raise ValueError("Empty response from Gemini")
    return text
