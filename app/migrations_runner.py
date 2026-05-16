"""Раннер SQL-миграций: применяет файлы из migrations/ в порядке номеров."""
import os
import time
from pathlib import Path

import psycopg2
import structlog

from .db import connect_db

logger = structlog.get_logger(__name__)

_MIGRATIONS_DIR = Path(__file__).parent.parent / "migrations"

_CREATE_TRACKING_TABLE = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version    TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""


def _wait_for_db(retries: int = 3, delay: float = 2.0):
    """Ожидает доступность БД с повторными попытками."""
    for attempt in range(1, retries + 1):
        try:
            conn = connect_db()
            conn.close()
            logger.info("соединение с БД установлено", attempt=attempt)
            return
        except psycopg2.OperationalError as exc:
            logger.warning(
                "БД недоступна, повтор через 2с",
                attempt=attempt,
                max_retries=retries,
                error=str(exc),
            )
            if attempt < retries:
                time.sleep(delay)
            else:
                raise RuntimeError(
                    f"Не удалось подключиться к БД после {retries} попыток"
                ) from exc


def run_migrations() -> list[str]:
    """
    Применяет все pending-миграции из каталога migrations/.
    Возвращает список применённых версий.
    """
    _wait_for_db()

    conn = connect_db()
    applied: list[str] = []
    try:
        with conn.cursor() as cur:
            cur.execute(_CREATE_TRACKING_TABLE)

            cur.execute("SELECT version FROM schema_migrations ORDER BY version")
            done = {row[0] for row in cur.fetchall()}

            sql_files = sorted(_MIGRATIONS_DIR.glob("*.sql"))
            if not sql_files:
                logger.warning("каталог migrations/ не содержит SQL-файлов")

            for path in sql_files:
                version = path.stem
                if version in done:
                    logger.info("миграция уже применена, пропуск", version=version)
                    continue

                sql = path.read_text(encoding="utf-8")
                cur.execute(sql)
                cur.execute(
                    "INSERT INTO schema_migrations (version) VALUES (%s)", (version,)
                )
                applied.append(version)
                logger.info("миграция применена", version=version)

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return applied
