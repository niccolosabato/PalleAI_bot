from collections import defaultdict
from typing import NamedTuple


class Member(NamedTuple):
    user_id: int
    name: str
    username: str | None


# chat_id -> {user_id: Member}
_members: dict[int, dict[int, Member]] = defaultdict(dict)


def record_member(chat_id: int, user_id: int, name: str, username: str | None) -> None:
    _members[chat_id][user_id] = Member(user_id, name, username)


def find_by_username(chat_id: int, username: str) -> Member | None:
    target = username.lower()
    return next(
        (member for member in _members[chat_id].values() if member.username and member.username.lower() == target),
        None,
    )
