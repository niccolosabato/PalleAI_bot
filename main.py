from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot online!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()

import logging

from telegram.ext import ApplicationBuilder

from bot.config import LOG_LEVEL, TELEGRAM_TOKEN
from bot.handlers import register_handlers


def main() -> None:
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=LOG_LEVEL,
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)

    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    register_handlers(application)

    application.run_polling(allowed_updates=["message"])


if __name__ == "__main__":
    main()
