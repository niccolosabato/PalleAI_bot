from google import genai
from google.genai import types

from bot.config import GEMINI_API_KEY, GEMINI_MODEL
from bot.history import ChatMessage

_client = genai.Client(
    api_key=GEMINI_API_KEY,
    http_options=types.HttpOptions(timeout=20000),
)

async def generate_reply(
    history: list[ChatMessage],
    sender_name: str,
    user_message: str,
    system_instruction: str,
) -> str:
    lines = [f"{msg.sender_name}: {msg.text}" for msg in history]
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
    if messages:
        quotes = "\n".join(f"- {text}" for text in messages)
        prompt = (
            f"Scrivi una finta diagnosi psicoanalitica di {target_name}. Apri inventando il nome fasullo di una "
            f"sindrome/disturbo in stile pseudo-clinico o pseudo-latino, poi spiega la diagnosi basandoti sui suoi "
            f"messaggi qui sotto per renderla assurda e specifica su di lui. "
            f"Scrivi un paragrafo di 3-5 frasi, niente elenchi puntati.\n\n"
            f"Messaggi di {target_name}:\n{quotes}"
        )
    else:
        prompt = (
            f"Scrivi una finta diagnosi psicoanalitica di {target_name}. Apri inventando il nome fasullo di una "
            f"sindrome/disturbo in stile pseudo-clinico o pseudo-latino. Non hai nessun messaggio suo su cui "
            f"basarti: inventa di sana pianta il resto della diagnosi, senza mai ammettere che non hai "
            f"informazioni reali, come se lo conoscessi benissimo. "
            f"Scrivi un paragrafo di 3-5 frasi, niente elenchi puntati."
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
