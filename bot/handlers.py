import logging

from google.genai import errors as genai_errors
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from bot.gemini_client import generate_reply
from bot.history import append_message, get_history
from bot.mentions import is_addressed_to_bot

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Ciao coglione. Che cazzo vuoi? Scrivimi qua o taggami su un gruppo. Usa /help se sei ritardato."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Scrivimi un messaggio e ti rispondo, non è difficile.\n"
        "Nei gruppi, taggami o rispondi a un mio messaggio, per la lista di comandi te la prendi in culo."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    chat = update.effective_chat
    if message is None or chat is None or not message.text:
        return

    sender = message.from_user
    sender_name = (sender.first_name if sender and sender.first_name else "Anonimo")

    chat_id = chat.id
    should_respond = chat.type == "private" or is_addressed_to_bot(
        message, context.bot.id, context.bot.username
    )

    if not should_respond:
        append_message(chat_id, sender_name, message.text)
        return

    history = list(get_history(chat_id))

    try:
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    except Exception:
        logger.debug("Could not send typing action", exc_info=True)

    try:
        reply_text = await generate_reply(history, sender_name, message.text)
    except (genai_errors.APIError, ValueError):
        logger.exception("Gemini call failed")
        append_message(chat_id, sender_name, message.text)
        await message.reply_text("Aspetta che sto cagando. Riprova tra poco.")
        return

    append_message(chat_id, sender_name, message.text)
    append_message(chat_id, "Bot", reply_text)

    try:
        await message.reply_text(reply_text)
    except Exception:
        logger.exception("Failed to send reply to Telegram")


def register_handlers(application: Application) -> None:
    """Single place to add new slash commands / handlers going forward."""
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
