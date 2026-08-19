import logging
import os
from threading import Thread

from flask import Flask
from telegram.ext import ApplicationBuilder

from bot.config import LOG_LEVEL, TELEGRAM_TOKEN
from bot.handlers import register_handlers

app = Flask("")


@app.route("/")
def home():
    return "Bot online!"


def keep_alive() -> None:
    """Apre una porta HTTP fittizia: su Render (piano free / Web Service) serve
    a passare l'health check sulla porta, altrimenti il servizio viene riavviato
    in loop e più istanze finiscono a fare polling in contemporanea (Conflict)."""
    port = int(os.getenv("PORT", "8080"))
    Thread(target=lambda: app.run(host="0.0.0.0", port=port), daemon=True).start()


def main() -> None:
    keep_alive()

    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=LOG_LEVEL,
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)

    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    register_handlers(application)

    application.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
