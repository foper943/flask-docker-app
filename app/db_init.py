import structlog

from .db import connect_db

logger = structlog.get_logger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            SERIAL PRIMARY KEY,
    email         TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name          TEXT NOT NULL,
    bio           TEXT,
    avatar_url    TEXT,
    role          TEXT NOT NULL DEFAULT 'learner',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS skills (
    id          SERIAL PRIMARY KEY,
    name        TEXT UNIQUE NOT NULL,
    category    TEXT NOT NULL,
    description TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_skills (
    id       SERIAL PRIMARY KEY,
    user_id  INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    skill_id INTEGER NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    type     TEXT NOT NULL,
    UNIQUE(user_id, skill_id, type)
);

CREATE TABLE IF NOT EXISTS sessions (
    id           SERIAL PRIMARY KEY,
    mentor_id    INTEGER NOT NULL REFERENCES users(id),
    learner_id   INTEGER NOT NULL REFERENCES users(id),
    skill_id     INTEGER NOT NULL REFERENCES skills(id),
    status       TEXT NOT NULL DEFAULT 'pending',
    scheduled_at TIMESTAMPTZ NOT NULL,
    topic        TEXT NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id          SERIAL PRIMARY KEY,
    sender_id   INTEGER NOT NULL REFERENCES users(id),
    receiver_id INTEGER NOT NULL REFERENCES users(id),
    text        TEXT NOT NULL,
    is_read     BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS reviews (
    id          SERIAL PRIMARY KEY,
    reviewer_id INTEGER NOT NULL REFERENCES users(id),
    reviewee_id INTEGER NOT NULL REFERENCES users(id),
    session_id  INTEGER NOT NULL REFERENCES sessions(id),
    rating      INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment     TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(reviewer_id, session_id)
);
"""

_SEED_SKILLS = [
    ("Python",          "Программирование", "Язык программирования Python"),
    ("JavaScript",      "Программирование", "JavaScript и экосистема Node.js"),
    ("React",           "Программирование", "Библиотека для построения UI"),
    ("Machine Learning","Data Science",     "Основы ML и нейронных сетей"),
    ("SQL",             "Базы данных",      "Реляционные базы данных и SQL"),
    ("Docker",          "DevOps",           "Контейнеризация приложений"),
    ("Git",             "Инструменты",      "Система контроля версий"),
    ("English",         "Языки",            "Английский язык"),
]


def ensure_all_tables() -> None:
    conn = connect_db()
    try:
        with conn.cursor() as cur:
            cur.execute(_SCHEMA)
            cur.execute("SELECT COUNT(*) FROM skills")
            if cur.fetchone()[0] == 0:
                cur.executemany(
                    "INSERT INTO skills (name, category, description) VALUES (%s, %s, %s)",
                    _SEED_SKILLS,
                )
        conn.commit()
        logger.info("database schema ready")
    finally:
        conn.close()
