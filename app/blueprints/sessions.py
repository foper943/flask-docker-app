import structlog
from flask import Blueprint, g, jsonify, request

from app.auth_utils import require_auth
from app.db import connect_db

logger = structlog.get_logger(__name__)
bp = Blueprint("sessions", __name__, url_prefix="/api/sessions")

_VALID_STATUSES = {"pending", "confirmed", "completed", "cancelled"}


def _session(row) -> dict:
    return {
        "id": row[0],
        "mentor_id": row[1],
        "mentor_name": row[2],
        "learner_id": row[3],
        "learner_name": row[4],
        "skill_id": row[5],
        "skill_name": row[6],
        "status": row[7],
        "scheduled_at": row[8].isoformat() if row[8] else None,
        "topic": row[9],
        "created_at": row[10].isoformat() if row[10] else None,
    }


_QUERY = """
    SELECT s.id,
           s.mentor_id,  m.name AS mentor_name,
           s.learner_id, l.name AS learner_name,
           s.skill_id,   sk.name AS skill_name,
           s.status, s.scheduled_at, s.topic, s.created_at
    FROM sessions s
    JOIN users m  ON m.id  = s.mentor_id
    JOIN users l  ON l.id  = s.learner_id
    JOIN skills sk ON sk.id = s.skill_id
"""


@bp.route("")
@require_auth
def list_sessions():
    uid = g.current_user_id
    conn = connect_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                _QUERY + " WHERE (s.mentor_id = %s OR s.learner_id = %s) ORDER BY s.scheduled_at",
                (uid, uid),
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    upcoming, past, pending = [], [], []
    for r in rows:
        sess = _session(r)
        if sess["status"] == "pending":
            pending.append(sess)
        elif sess["status"] in ("confirmed",):
            upcoming.append(sess)
        else:
            past.append(sess)

    return jsonify({"upcoming": upcoming, "past": past, "pending": pending})


@bp.route("", methods=["POST"])
@require_auth
def create_session():
    data = request.get_json() or {}
    mentor_id = data.get("mentor_id")
    skill_id = data.get("skill_id")
    scheduled_at = data.get("scheduled_at")
    topic = (data.get("topic") or "").strip()

    if not all([mentor_id, skill_id, scheduled_at, topic]):
        return jsonify({"error": "mentor_id, skill_id, scheduled_at и topic обязательны"}), 400
    if mentor_id == g.current_user_id:
        return jsonify({"error": "нельзя записаться на сессию к самому себе"}), 422

    conn = connect_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO sessions (mentor_id, learner_id, skill_id, scheduled_at, topic)
                   VALUES (%s, %s, %s, %s, %s)
                   RETURNING id""",
                (mentor_id, g.current_user_id, skill_id, scheduled_at, topic),
            )
            session_id = cur.fetchone()[0]
            cur.execute(_QUERY + " WHERE s.id = %s", (session_id,))
            sess = _session(cur.fetchone())
        conn.commit()
    finally:
        conn.close()

    logger.info("session created", session_id=session_id)
    return jsonify({"session": sess}), 201


@bp.route("/<int:session_id>", methods=["PUT"])
@require_auth
def update_session(session_id: int):
    data = request.get_json() or {}
    status = data.get("status")

    if status not in _VALID_STATUSES:
        return jsonify({"error": f"status должен быть одним из: {', '.join(_VALID_STATUSES)}"}), 400

    conn = connect_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT mentor_id, learner_id FROM sessions WHERE id = %s", (session_id,)
            )
            row = cur.fetchone()
            if not row:
                return jsonify({"error": "сессия не найдена"}), 404
            if g.current_user_id not in (row[0], row[1]):
                return jsonify({"error": "нет доступа к этой сессии"}), 403

            cur.execute(
                "UPDATE sessions SET status = %s WHERE id = %s", (status, session_id)
            )
            cur.execute(_QUERY + " WHERE s.id = %s", (session_id,))
            sess = _session(cur.fetchone())
        conn.commit()
    finally:
        conn.close()

    return jsonify({"session": sess})
