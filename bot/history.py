from collections import defaultdict

from bot.config import MAX_HISTORY_MESSAGES

# chat_id -> list of (sender_name, text)
_histories: dict[int, list[tuple[str, str]]] = defaultdict(list)


def get_history(chat_id: int) -> list[tuple[str, str]]:
    return _histories[chat_id]


def append_message(chat_id: int, sender_name: str, text: str) -> None:
    history = _histories[chat_id]
    history.append((sender_name, text))
    if len(history) > MAX_HISTORY_MESSAGES:
        del history[: len(history) - MAX_HISTORY_MESSAGES]
