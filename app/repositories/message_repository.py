from typing import List

from ..db import connect_db
from .base import MessageRepositoryBase


class MessageRepository(MessageRepositoryBase):
    def ensure_table(self) -> None:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                text TEXT
            )
            """
        )
        conn.commit()
        conn.close()

    def insert(self, text: str) -> None:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO messages (text) VALUES (%s)", (text,))
        conn.commit()
        conn.close()

    def get_last(self) -> str:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT text FROM messages ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else ""

    def get_all(self) -> List[str]:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT text FROM messages")
        rows = cursor.fetchall()
        conn.close()
        return [row[0] for row in rows]
