from .db import connect_db
import redis
import os

r = redis.Redis(host=os.getenv("REDIS_HOST", "localhost"), port=6379)

def get_message():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            text TEXT
        )
    """)

    cursor.execute("INSERT INTO messages (text) VALUES ('Hello from PostgreSQL')")
    conn.commit()

    cursor.execute("SELECT text FROM messages ORDER BY id DESC LIMIT 1")
    result = cursor.fetchone()

    conn.close()

    return result[0]

def get_all_messages():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT text FROM messages")
    result = cursor.fetchall()

    conn.close()

    return [row[0] for row in result]

def add_message(text):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO messages (text) VALUES (%s)",
        (text,)
    )
    conn.commit()
    conn.close()

def add_counter():
    return r.incr("counter")