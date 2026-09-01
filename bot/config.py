import os

from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
# /chiedi usa la ricerca web (google_search grounding): i modelli "lite" spesso non
# la supportano, quindi di default si usa un flash pieno e un timeout più generoso.
GEMINI_ANSWER_MODEL = os.getenv("GEMINI_ANSWER_MODEL", "gemini-3.1-flash")
GEMINI_ANSWER_TIMEOUT_MS = int(os.getenv("GEMINI_ANSWER_TIMEOUT_MS", "60000"))

MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", "10"))

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
