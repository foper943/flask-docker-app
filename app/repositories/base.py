from abc import ABC, abstractmethod
from typing import List


class MessageRepositoryBase(ABC):
    @abstractmethod
    def ensure_table(self) -> None: ...

    @abstractmethod
    def insert(self, text: str) -> None: ...

    @abstractmethod
    def get_last(self) -> str: ...

    @abstractmethod
    def get_all(self) -> List[str]: ...


class CounterRepositoryBase(ABC):
    @abstractmethod
    def increment(self) -> int: ...
