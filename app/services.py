from typing import List

from .repositories.counter_repository import CounterRepository
from .repositories.message_repository import MessageRepository

_message_repo = MessageRepository()
_counter_repo = CounterRepository()


def get_message() -> str:
    _message_repo.insert("Hello from PostgreSQL")
    return _message_repo.get_last()


def get_all_messages() -> List[str]:
    return _message_repo.get_all()


def add_message(text: str) -> None:
    _message_repo.insert(text)


def add_counter() -> int:
    return _counter_repo.increment()
