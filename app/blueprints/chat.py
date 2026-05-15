import structlog
from flask import Blueprint, g, jsonify, request

from app.auth_utils import require_auth
from app.db import connect_db

logger = structlog.get_logger(__name__)
bp = Blueprint("chat", __name__, url_prefix="/api/chat")


@bp.route("")
@require_auth
def list_dialogs():
    uid = g.current_user_id
    conn = connect_db()
    try:
        with conn.cursor() as cur:
            # Один диалог на пару пользователей — берём последнее сообщение
            cur.execute(
                """
                WITH partners AS (
                    SELECT CASE WHEN sender_id = %s THEN receiver_id ELSE sender_id END AS partner_id
                    FROM chat_messages
                    WHERE sender_id = %s OR receiver_id = %s
                    GROUP BY partner_id
                ),
                last_msgs AS (
                    SELECT DISTINCT ON (
                        LEAST(sender_id, receiver_id), GREATEST(sender_id, receiver_id)
                    )
                        sender_id, receiver_id, text, created_at
                    FROM chat_messages
                    WHERE sender_id = %s OR receiver_id = %s
                    ORDER BY LEAST(sender_id, receiver_id),
                             GREATEST(sender_id, receiver_id),
                             created_at DESC
                ),
                unread AS (
                    SELECT sender_id, COUNT(*) AS cnt
                    FROM chat_messages
                    WHERE receiver_id = %s AND is_read = FALSE
                    GROUP BY sender_id
                )
                SELECT u.id, u.name, u.avatar_url,
                       lm.text, lm.created_at,
                       COALESCE(un.cnt, 0)
                FROM partners p
                JOIN users u ON u.id = p.partner_id
                JOIN last_msgs lm ON (
                    (lm.sender_id = u.id AND lm.receiver_id = %s)
                    OR (lm.sender_id = %s AND lm.receiver_id = u.id)
                )
                LEFT JOIN unread un ON un.sender_id = u.id
                ORDER BY lm.created_at DESC
                """,
                (uid, uid, uid, uid, uid, uid, uid, uid),
            )
            dialogs = [
                {
                    "user_id": r[0],
                    "user_name": r[1],
                    "user_avatar": r[2],
                    "last_message": r[3],
                    "last_message_at": r[4].isoformat() if r[4] else None,
                    "unread_count": r[5],
                }
                for r in cur.fetchall()
            ]
    finally:
        conn.close()

    return jsonify({"dialogs": dialogs})


@bp.route("/<int:other_id>")
@require_auth
def get_messages(other_id: int):
    uid = g.current_user_id
    conn = connect_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT id, sender_id, receiver_id, text, is_read, created_at
                   FROM chat_messages
                   WHERE (sender_id = %s AND receiver_id = %s)
                      OR (sender_id = %s AND receiver_id = %s)
                   ORDER BY created_at""",
                (uid, other_id, other_id, uid),
            )
            messages = [
                {
                    "id": r[0], "sender_id": r[1], "receiver_id": r[2],
                    "text": r[3], "is_read": r[4],
                    "created_at": r[5].isoformat() if r[5] else None,
                }
                for r in cur.fetchall()
            ]
            # Отмечаем входящие как прочитанные
            cur.execute(
                "UPDATE chat_messages SET is_read = TRUE WHERE sender_id = %s AND receiver_id = %s AND is_read = FALSE",
                (other_id, uid),
            )
        conn.commit()
    finally:
        conn.close()

    return jsonify({"messages": messages})


@bp.route("/<int:other_id>", methods=["POST"])
@require_auth
def send_message(other_id: int):
    uid = g.current_user_id
    data = request.get_json() or {}
    text = (data.get("text") or "").strip()

    if not text:
        return jsonify({"error": "text обязателен"}), 400

    conn = connect_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO chat_messages (sender_id, receiver_id, text)
                   VALUES (%s, %s, %s)
                   RETURNING id, sender_id, receiver_id, text, is_read, created_at""",
                (uid, other_id, text),
            )
            r = cur.fetchone()
            message = {
                "id": r[0], "sender_id": r[1], "receiver_id": r[2],
                "text": r[3], "is_read": r[4],
                "created_at": r[5].isoformat() if r[5] else None,
            }
        conn.commit()
    finally:
        conn.close()

    return jsonify({"message": message}), 201
