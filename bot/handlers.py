import logging

from google.genai import errors as genai_errors
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LinkPreviewOptions,
    Update,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from bot.gemini_client import (
    generate_answer,
    generate_psychoanalysis,
    generate_reply,
    generate_rissa,
)
from bot.history import append_message, get_history
from bot.members import find_by_username, record_member
from bot.mentions import is_addressed_to_bot
from bot.personalities import (
    ASSISTANT_INSTRUCTION,
    PERSONALITIES,
    PSYCHOANALYST_INSTRUCTION,
    RISSA_INSTRUCTION,
    get_active_personality,
    set_active_personality,
)

_NO_LINK_PREVIEW = LinkPreviewOptions(is_disabled=True)
_TELEGRAM_MAX = 4000

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Ciao coglione. Che cazzo vuoi? Scrivimi qua o taggami su un gruppo. Usa /help se sei ritardato."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Scrivimi un messaggio e ti rispondo, non è difficile.\n"
        "Nei gruppi, taggami o rispondi a un mio messaggio.\n"
        "/chiedi <domanda> se ti serve una risposta vera (cerco pure sul web), /persona per cambiarmi il "
        "carattere, /psicoanalizza e /rissa per il resto."
    )


async def chiedi_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Risposta utile (ma sempre da stronzo) a una domanda, con ricerca web di Gemini.

    Una tantum: non cambia la personalità attiva della chat.
    """
    message = update.effective_message
    chat_id = update.effective_chat.id

    question = " ".join(context.args).strip() if context.args else ""
    reply = message.reply_to_message
    if reply and reply.text:
        quoted = reply.text.strip()
        question = f"{question}\n\n[messaggio citato] {quoted}".strip() if question else quoted

    if not question:
        await message.reply_text(
            "E chiedimi qualcosa, genio. Tipo /chiedi quanto è alto l'Everest, "
            "oppure rispondi a un messaggio con /chiedi."
        )
        return

    history = list(get_history(chat_id))

    placeholder = await message.reply_text("Aspetta che ci penso, coglione...")

    try:
        answer = await generate_answer(question, ASSISTANT_INSTRUCTION, history)
    except Exception as exc:
        logger.exception("Gemini answer call failed: %r", exc)
        await placeholder.edit_text("Aspetta che sto cagando. Riprova tra poco.")
        return

    try:
        await placeholder.delete()
    except Exception:
        logger.debug("Could not delete placeholder message", exc_info=True)

    sender = message.from_user
    sender_name = sender.first_name if sender and sender.first_name else "Anonimo"
    append_message(
        chat_id,
        sender_name,
        sender.username if sender else None,
        sender.id if sender else 0,
        f"/chiedi {question}",
    )

    for i in range(0, len(answer), _TELEGRAM_MAX):
        await message.reply_text(
            answer[i : i + _TELEGRAM_MAX], link_preview_options=_NO_LINK_PREVIEW
        )


async def persona_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    current = get_active_personality(chat_id)
    keyboard = [
        [
            InlineKeyboardButton(
                ("✅ " if key == current else "") + personality.display_name,
                callback_data=f"persona:{key}",
            )
        ]
        for key, personality in PERSONALITIES.items()
    ]
    await update.message.reply_text(
        "Scegli la personalità del bot:", reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def persona_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    key = query.data.split(":", 1)[1]
    if key not in PERSONALITIES:
        return
    set_active_personality(update.effective_chat.id, key)
    await query.edit_message_text(f"Personalità impostata: {PERSONALITIES[key].display_name}")


async def psicoanalizza_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    chat_id = update.effective_chat.id
    history = get_history(chat_id)

    target_user_id: int | None = None

    if context.args:
        # Argomento esplicito: si intende come username Telegram, non il nome visualizzato.
        username_query = " ".join(context.args).lstrip("@").lower()
        target_name = f"@{username_query}"
        match = next(
            (msg for msg in history if msg.username and msg.username.lower() == username_query),
            None,
        )
        if match:
            target_user_id = match.user_id
            target_name = match.sender_name
    elif message.reply_to_message and message.reply_to_message.from_user:
        target_user = message.reply_to_message.from_user
        target_user_id = target_user.id
        target_name = target_user.first_name or "Anonimo"
    else:
        target_user = message.from_user
        target_user_id = target_user.id if target_user else None
        target_name = target_user.first_name if target_user and target_user.first_name else "Anonimo"

    messages = (
        [msg.text for msg in history if msg.user_id == target_user_id]
        if target_user_id is not None
        else []
    )

    try:
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    except Exception:
        logger.debug("Could not send typing action", exc_info=True)

    try:
        analysis = await generate_psychoanalysis(
            target_name, messages, PSYCHOANALYST_INSTRUCTION
        )
    except (genai_errors.APIError, ValueError):
        logger.exception("Gemini psychoanalysis call failed")
        await message.reply_text("Aspetta che sto cagando. Riprova tra poco.")
        return

    await message.reply_text(analysis)


def _resolve_mention(chat_id: int, raw: str) -> tuple[str, str | int]:
    """Risolve un '@nick' passato come argomento a un nome visualizzato + identità univoca.

    Niente '@' nel fallback: un '@nickname' nel testo verrebbe interpretato da Telegram
    come una mention vera, notificando quella persona.
    """
    username = raw.lstrip("@")
    member = find_by_username(chat_id, username)
    if member:
        return member.name, member.user_id
    return username, username


def _resolve_user(user) -> tuple[str, str | int]:
    name = user.first_name if user and user.first_name else "Anonimo"
    identity: str | int = user.id if user else name
    return name, identity


async def rissa_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    chat_id = update.effective_chat.id
    args = context.args or []
    has_reply = bool(message.reply_to_message and message.reply_to_message.from_user)

    if len(args) >= 2:
        name1, id1 = _resolve_mention(chat_id, args[0])
        name2, id2 = _resolve_mention(chat_id, args[1])
    elif len(args) == 1:
        if has_reply:
            name1, id1 = _resolve_user(message.reply_to_message.from_user)
        else:
            name1, id1 = _resolve_user(message.from_user)
        name2, id2 = _resolve_mention(chat_id, args[0])
    elif has_reply:
        name1, id1 = _resolve_user(message.from_user)
        name2, id2 = _resolve_user(message.reply_to_message.from_user)
    else:
        await message.reply_text(
            "Dimmi almeno con chi deve litigare, tipo /rissa @tizio o /rissa @tizio @caio, "
            "oppure rispondi a un messaggio con /rissa."
        )
        return

    if id1 == id2:
        await message.reply_text("Vuoi farlo litigare da solo? Trovati un nemico vero.")
        return

    try:
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    except Exception:
        logger.debug("Could not send typing action", exc_info=True)

    try:
        rissa_text = await generate_rissa(name1, name2, RISSA_INSTRUCTION)
    except (genai_errors.APIError, ValueError):
        logger.exception("Gemini rissa call failed")
        await message.reply_text("Aspetta che sto cagando. Riprova tra poco.")
        return

    await message.reply_text(rissa_text)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    chat = update.effective_chat
    if message is None or chat is None or not message.text:
        return

    sender = message.from_user
    sender_name = (sender.first_name if sender and sender.first_name else "Anonimo")
    sender_username = sender.username if sender else None
    sender_id = sender.id if sender else 0

    chat_id = chat.id
    record_member(chat_id, sender_id, sender_name, sender_username)
    should_respond = chat.type == "private" or is_addressed_to_bot(
        message, context.bot.id, context.bot.username
    )

    if not should_respond:
        append_message(chat_id, sender_name, sender_username, sender_id, message.text)
        return

    history = list(get_history(chat_id))

    try:
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    except Exception:
        logger.debug("Could not send typing action", exc_info=True)

    system_instruction = PERSONALITIES[get_active_personality(chat_id)].instruction

    try:
        reply_text = await generate_reply(history, sender_name, message.text, system_instruction)
    except (genai_errors.APIError, ValueError):
        logger.exception("Gemini call failed")
        append_message(chat_id, sender_name, sender_username, sender_id, message.text)
        await message.reply_text("Aspetta che sto cagando. Riprova tra poco.")
        return

    append_message(chat_id, sender_name, sender_username, sender_id, message.text)
    append_message(chat_id, "Bot", context.bot.username, context.bot.id, reply_text)

    try:
        await message.reply_text(reply_text)
    except Exception:
        logger.exception("Failed to send reply to Telegram")


def register_handlers(application: Application) -> None:
    """Single place to add new slash commands / handlers going forward."""
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("chiedi", chiedi_command))
    application.add_handler(CommandHandler("persona", persona_command))
    application.add_handler(CommandHandler("psicoanalizza", psicoanalizza_command))
    application.add_handler(CommandHandler("rissa", rissa_command))
    application.add_handler(CallbackQueryHandler(persona_callback, pattern=r"^persona:"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
