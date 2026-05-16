from .base import CounterRepositoryBase
from ..db import connect_redis


class CounterRepository(CounterRepositoryBase):
    def __init__(self) -> None:
        self._redis = connect_redis()

    def increment(self) -> int:
        return self._redis.incr("counter")
