from telegram import Message, MessageEntity


def is_addressed_to_bot(message: Message, bot_id: int, bot_username: str) -> bool:
    """True if the bot should respond to this group message."""
    if (
        message.reply_to_message
        and message.reply_to_message.from_user
        and message.reply_to_message.from_user.id == bot_id
    ):
        return True

    if message.entities and message.text:
        target = f"@{bot_username}".lower()
        for entity in message.entities:
            if entity.type == MessageEntity.MENTION:
                mention_text = message.text[entity.offset : entity.offset + entity.length]
                if mention_text.lower() == target:
                    return True

    return False
