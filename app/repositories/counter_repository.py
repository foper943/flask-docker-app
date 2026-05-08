import os

import redis

from .base import CounterRepositoryBase


class CounterRepository(CounterRepositoryBase):
    def __init__(self) -> None:
        self._redis = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"), port=6379
        )

    def increment(self) -> int:
        return self._redis.incr("counter")
