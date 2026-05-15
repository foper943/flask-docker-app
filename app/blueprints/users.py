import structlog
from flask import Blueprint, g, jsonify, request

from app.auth_utils import require_auth
from app.db import connect_db

logger = structlog.get_logger(__name__)
bp = Blueprint("users", __name__, url_prefix="/api/users")


def _user(row) -> dict:
    return {
        "id": row[0],
        "email": row[1],
        "name": row[2],
        "bio": row[3],
        "avatar_url": row[4],
        "role": row[5],
        "created_at": row[6].isoformat() if row[6] else None,
    }


def _skills_for_user(cur, user_id: int) -> list:
    cur.execute(
        """SELECT us.skill_id, s.name, s.category, us.type
           FROM user_skills us
           JOIN skills s ON s.id = us.skill_id
           WHERE us.user_id = %s""",
        (user_id,),
    )
    return [
        {"skill_id": r[0], "skill_name": r[1], "skill_category": r[2], "type": r[3]}
        for r in cur.fetchall()
    ]


@bp.route("/<int:user_id>")
def get_user(user_id: int):
    conn = connect_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, email, name, bio, avatar_url, role, created_at FROM users WHERE id = %s",
                (user_id,),
            )
            row = cur.fetchone()
            if not row:
                return jsonify({"error": "пользователь не найден"}), 404
            user = _user(row)
            user["skills"] = _skills_for_user(cur, user_id)
    finally:
        conn.close()

    return jsonify({"user": user})


@bp.route("/<int:user_id>", methods=["PUT"])
@require_auth
def update_user(user_id: int):
    if g.current_user_id != user_id:
        return jsonify({"error": "нельзя редактировать чужой профиль"}), 403

    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    bio = data.get("bio")
    avatar_url = data.get("avatar_url")
    role = data.get("role", "learner")
    teaching_skills: list[int] = data.get("teaching_skills") or []
    learning_skills: list[int] = data.get("learning_skills") or []

    if not name:
        return jsonify({"error": "name обязателен"}), 400
    if role not in ("mentor", "learner", "both"):
        return jsonify({"error": "role должен быть mentor / learner / both"}), 400

    conn = connect_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE users SET name=%s, bio=%s, avatar_url=%s, role=%s WHERE id=%s
                   RETURNING id, email, name, bio, avatar_url, role, created_at""",
                (name, bio, avatar_url, role, user_id),
            )
            row = cur.fetchone()
            if not row:
                return jsonify({"error": "пользователь не найден"}), 404
            user = _user(row)

            # Пересохраняем навыки полностью
            cur.execute("DELETE FROM user_skills WHERE user_id = %s", (user_id,))
            for skill_id in teaching_skills:
                cur.execute(
                    "INSERT INTO user_skills (user_id, skill_id, type) VALUES (%s, %s, 'teaching') ON CONFLICT DO NOTHING",
                    (user_id, skill_id),
                )
            for skill_id in learning_skills:
                cur.execute(
                    "INSERT INTO user_skills (user_id, skill_id, type) VALUES (%s, %s, 'learning') ON CONFLICT DO NOTHING",
                    (user_id, skill_id),
                )

            user["skills"] = _skills_for_user(cur, user_id)
        conn.commit()
    finally:
        conn.close()

    return jsonify({"user": user})
