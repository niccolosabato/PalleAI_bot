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


def _extract_sources(response) -> list[str]:
    """URL delle fonti citate dal grounding di Gemini, se la ricerca web è stata usata."""
    try:
        chunks = response.candidates[0].grounding_metadata.grounding_chunks or []
    except (AttributeError, IndexError, TypeError):
        return []
    urls: list[str] = []
    for chunk in chunks:
        uri = getattr(getattr(chunk, "web", None), "uri", None)
        if uri and uri not in urls:
            urls.append(uri)
    return urls[:5]


async def generate_answer(
    question: str,
    system_instruction: str,
    history: list[ChatMessage] | None = None,
) -> str:
    parts = []
    if history:
        context_lines = "\n".join(f"{msg.sender_name}: {msg.text}" for msg in history)
        parts.append(
            "Contesto recente della chat (usalo solo se serve a capire la domanda):\n"
            f"{context_lines}"
        )
    parts.append(f"Domanda:\n{question}")

    response = await _client.aio.models.generate_content(
        model=GEMINI_MODEL,
        contents=[{"role": "user", "parts": [{"text": "\n\n".join(parts)}]}],
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=[types.Tool(google_search=types.GoogleSearch())],
        ),
    )
    text = getattr(response, "text", None)
    if not text:
        raise ValueError("Empty response from Gemini")

    sources = _extract_sources(response)
    if sources:
        text += "\n\nFonti:\n" + "\n".join(f"- {url}" for url in sources)
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


async def generate_rissa(name1: str, name2: str, system_instruction: str) -> str:
    prompt = (
        f"Genera una scazzottata immaginaria, inventata di sana pianta, tra {name1} e {name2}. "
        f"Scrivi mosse fisiche alternate a righe nel formato \"Nome: mossa\", cominciando da {name1}, "
        f"per un totale di 6-8 righe (3-4 mosse a testa), seguite da un'ultima riga che dichiara il vincitore "
        f"tra {name1} e {name2}, oppure un pareggio. Ogni riga deve essere una sola frase corta e diretta."
    )

    response = await _client.aio.models.generate_content(
        model=GEMINI_MODEL,
        contents=[{"role": "user", "parts": [{"text": prompt}]}],
        config=types.GenerateContentConfig(system_instruction=system_instruction),
    )
    text = getattr(response, "text", None)
    if not text:
        raise ValueError("Empty response from Gemini")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n\n".join(lines)
