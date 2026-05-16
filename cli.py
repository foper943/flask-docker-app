"""
Административный CLI платформы взаимного обучения.

Использование:
  python cli.py server          # запуск Flask-сервера через gunicorn
  python cli.py migrate         # применение SQL-миграций
  python cli.py create-admin    # создание администратора
  python cli.py clear-cache     # очистка Redis-кэша
"""
import os
import signal
import sys

import click
from dotenv import load_dotenv

load_dotenv()


def _setup_logging():
    from app.logging_config import configure_logging
    configure_logging(os.getenv("SERVICE_NAME", "cli"))


@click.group()
def cli():
    """Административные команды платформы взаимного обучения."""


# ---------------------------------------------------------------------------
# server
# ---------------------------------------------------------------------------

@cli.command()
def server():
    """Запуск Flask-сервера через gunicorn (основной режим работы)."""
    _setup_logging()
    import structlog
    logger = structlog.get_logger(__name__)
    logger.info("запуск сервера", mode="gunicorn")

    import subprocess

    proc = subprocess.Popen(
        ["gunicorn", "--config", "gunicorn.conf.py", "run:app"],
    )

    def _shutdown(signum, frame):
        proc.send_signal(signum)

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    sys.exit(proc.wait())


# ---------------------------------------------------------------------------
# migrate
# ---------------------------------------------------------------------------

@cli.command()
def migrate():
    """Применение всех pending SQL-миграций. Идемпотентно."""
    _setup_logging()
    import structlog
    logger = structlog.get_logger(__name__)

    try:
        from app.migrations_runner import run_migrations
        applied = run_migrations()
        if applied:
            logger.info(
                "миграции успешно применены",
                count=len(applied),
                versions=applied,
            )
        else:
            logger.info("нет новых миграций для применения")
        sys.exit(0)
    except Exception as exc:
        import structlog as _sl
        _sl.get_logger(__name__).error("ошибка применения миграций", error=str(exc))
        sys.exit(1)


# ---------------------------------------------------------------------------
# create-admin
# ---------------------------------------------------------------------------

@cli.command("create-admin")
@click.option("--email", required=True, help="Email администратора")
@click.option("--password", required=True, help="Пароль администратора")
@click.option("--name", default="Администратор", show_default=True, help="Имя пользователя")
def create_admin(email: str, password: str, name: str):
    """Создание пользователя с ролью admin."""
    _setup_logging()
    import structlog
    logger = structlog.get_logger(__name__)

    try:
        from werkzeug.security import generate_password_hash
        from app.db import connect_db

        conn = connect_db()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM users WHERE email = %s", (email,))
                existing = cur.fetchone()
                if existing:
                    logger.warning("пользователь уже существует", email=email)
                    sys.exit(1)

                cur.execute(
                    """INSERT INTO users (email, password_hash, name, role)
                       VALUES (%s, %s, %s, 'admin')
                       RETURNING id""",
                    (email, generate_password_hash(password), name),
                )
                user_id = cur.fetchone()[0]
            conn.commit()
        finally:
            conn.close()

        logger.info("администратор создан", email=email, user_id=user_id)
        sys.exit(0)
    except Exception as exc:
        import structlog as _sl
        _sl.get_logger(__name__).error("ошибка создания администратора", error=str(exc))
        sys.exit(1)


# ---------------------------------------------------------------------------
# clear-cache
# ---------------------------------------------------------------------------

@cli.command("clear-cache")
def clear_cache():
    """Полная очистка Redis-кэша."""
    _setup_logging()
    import structlog
    logger = structlog.get_logger(__name__)

    try:
        from app.db import connect_redis
        r = connect_redis()
        r.flushdb()
        logger.info("Redis-кэш успешно очищен")
        sys.exit(0)
    except Exception as exc:
        import structlog as _sl
        _sl.get_logger(__name__).error("ошибка очистки кэша", error=str(exc))
        sys.exit(1)


# ---------------------------------------------------------------------------
# seed
# ---------------------------------------------------------------------------

@cli.command()
def seed():
    """Наполнение БД тестовыми данными (пользователи, сессии, отзывы)."""
    _setup_logging()
    import structlog
    logger = structlog.get_logger(__name__)

    try:
        from app.migrations_runner import run_migrations
        applied = run_migrations()
        if applied:
            logger.info("применены миграции перед seed", versions=applied)
        logger.info("тестовые данные успешно загружены")
        sys.exit(0)
    except Exception as exc:
        import structlog as _sl
        _sl.get_logger(__name__).error("ошибка загрузки тестовых данных", error=str(exc))
        sys.exit(1)


if __name__ == "__main__":
    cli()
