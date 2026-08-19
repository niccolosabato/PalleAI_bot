from collections import defaultdict
from typing import NamedTuple

from bot.config import MAX_HISTORY_MESSAGES


class ChatMessage(NamedTuple):
    sender_name: str
    username: str | None
    user_id: int
    text: str


# chat_id -> list of ChatMessage
_histories: dict[int, list[ChatMessage]] = defaultdict(list)


def get_history(chat_id: int) -> list[ChatMessage]:
    return _histories[chat_id]


def append_message(
    chat_id: int, sender_name: str, username: str | None, user_id: int, text: str
) -> None:
    history = _histories[chat_id]
    history.append(ChatMessage(sender_name, username, user_id, text))
    if len(history) > MAX_HISTORY_MESSAGES:
        del history[: len(history) - MAX_HISTORY_MESSAGES]
