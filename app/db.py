import os

import psycopg2


def connect_db():
    """Подключение к БД: DATABASE_URL имеет приоритет над отдельными переменными."""
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return psycopg2.connect(database_url)
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 5432)),
        dbname=os.getenv("DB_NAME", "mydb"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
    )


def connect_redis():
    """Подключение к Redis: REDIS_URL имеет приоритет над REDIS_HOST."""
    import redis

    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        return redis.from_url(redis_url)
    return redis.Redis(host=os.getenv("REDIS_HOST", "localhost"), port=6379)
