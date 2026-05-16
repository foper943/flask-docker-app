"""WebSocket-события чата через Flask-SocketIO."""
import structlog
from flask_socketio import SocketIO, emit, join_room, leave_room

from app.auth_utils import decode_token
from app.db import connect_db

logger = structlog.get_logger(__name__)

socketio = SocketIO(cors_allowed_origins="*", async_mode="gevent")


def _room(uid: int) -> str:
    """Личная комната пользователя — получает все входящие сообщения."""
    return f"user_{uid}"


@socketio.on("connect")
def on_connect(auth):
    """Аутентификация по JWT при подключении."""
    token = (auth or {}).get("token", "")
    try:
        uid = decode_token(token)
        join_room(_room(uid))
        logger.info("websocket: пользователь подключён", user_id=uid)
    except Exception:
        logger.warning("websocket: неверный токен при подключении")
        return False  # отклонить соединение


@socketio.on("disconnect")
def on_disconnect():
    logger.info("websocket: пользователь отключён")


@socketio.on("send_message")
def on_send_message(data):
    """
    Клиент отправляет: {token, receiver_id, text}
    Сервер сохраняет в БД и доставляет получателю в реальном времени.
    """
    token = (data or {}).get("token", "")
    try:
        sender_id = decode_token(token)
    except Exception:
        emit("error", {"message": "не авторизован"})
        return

    receiver_id = data.get("receiver_id")
    text = (data.get("text") or "").strip()

    if not receiver_id or not text:
        emit("error", {"message": "receiver_id и text обязательны"})
        return

    conn = connect_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO chat_messages (sender_id, receiver_id, text)
                   VALUES (%s, %s, %s)
                   RETURNING id, sender_id, receiver_id, text, is_read, created_at""",
                (sender_id, receiver_id, text),
            )
            r = cur.fetchone()
            message = {
                "id": r[0],
                "sender_id": r[1],
                "receiver_id": r[2],
                "text": r[3],
                "is_read": r[4],
                "created_at": r[5].isoformat() if r[5] else None,
            }
        conn.commit()
    except Exception as exc:
        conn.rollback()
        logger.error("websocket: ошибка сохранения сообщения", error=str(exc))
        emit("error", {"message": "ошибка сервера"})
        return
    finally:
        conn.close()

    # Доставить отправителю (эхо) и получателю
    emit("new_message", message, room=_room(sender_id))
    if receiver_id != sender_id:
        emit("new_message", message, room=_room(receiver_id))

    logger.info("websocket: сообщение отправлено", sender_id=sender_id, receiver_id=receiver_id)


@socketio.on("mark_read")
def on_mark_read(data):
    """Отметить все сообщения от sender_id как прочитанные."""
    token = (data or {}).get("token", "")
    try:
        uid = decode_token(token)
    except Exception:
        return

    sender_id = data.get("sender_id")
    if not sender_id:
        return

    conn = connect_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE chat_messages SET is_read = TRUE WHERE sender_id = %s AND receiver_id = %s AND is_read = FALSE",
                (sender_id, uid),
            )
        conn.commit()
    finally:
        conn.close()
