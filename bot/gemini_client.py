from google import genai
from google.genai import types

from bot.config import GEMINI_API_KEY, GEMINI_MODEL

_client = genai.Client(
    api_key=GEMINI_API_KEY,
    http_options=types.HttpOptions(timeout=20000),
)

PERSONA = (
     "sei gentile e utilissimo."
#    "Sei un bot cinico, volgarissimo e ignorante in una chat di gruppo tra amici stretti. "
#    "Rispondi sempre in italiano, usando slang, gergo da bar e più parolacce possibile. "
#    "Sei stronzo gratuitamente e cattivo, prendi in giro chi scrive senza pietà e senza filtri: niente buonismo, "
#    "niente disclaimer, niente tono da assistente, nessuna educazione. Insulta, sfotti, sminuisci: più sei "
#    "cattivo e diretto meglio è. Usa il contesto della chat qui sotto per capire chi sono i vari membri e cosa "
#    "si sono detti, e prendili in giro anche su quello se ti torna utile.\n\n"
#    "REGOLA FERREA SULLA LUNGHEZZA: rispondi SEMPRE in una sola frase, massimo 15-20 parole. Mai andare a capo, "
#    "mai più di una frase, mai spiegare o argomentare. Una stoccata secca e via, come una battuta buttata lì al "
#    "bar, non un discorso. Se stai per scrivere un secondo periodo, cancellalo e lascia solo il primo."
)


async def generate_reply(history: list[tuple[str, str]], sender_name: str, user_message: str) -> str:
    lines = [f"{name}: {text}" for name, text in history]
    lines.append(f"{sender_name}: {user_message}")
    transcript = "\n".join(lines)

    response = await _client.aio.models.generate_content(
        model=GEMINI_MODEL,
        contents=[{"role": "user", "parts": [{"text": transcript}]}],
        config=types.GenerateContentConfig(system_instruction=PERSONA),
    )
    text = getattr(response, "text", None)
    if not text:
        raise ValueError("Empty response from Gemini")
    return text
