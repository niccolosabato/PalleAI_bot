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

    application.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
