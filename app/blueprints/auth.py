import structlog
from flask import Blueprint, g, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from app.auth_utils import encode_token, require_auth
from app.db import connect_db

logger = structlog.get_logger(__name__)
bp = Blueprint("auth", __name__, url_prefix="/api/auth")


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


@bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""
    name = (data.get("name") or "").strip()

    if not email or not password or not name:
        return jsonify({"error": "email, password и name обязательны"}), 400

    conn = connect_db()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cur.fetchone():
                return jsonify({"error": "email уже зарегистрирован"}), 409

            cur.execute(
                """INSERT INTO users (email, password_hash, name)
                   VALUES (%s, %s, %s)
                   RETURNING id, email, name, bio, avatar_url, role, created_at""",
                (email, generate_password_hash(password), name),
            )
            user = _user(cur.fetchone())
        conn.commit()
    finally:
        conn.close()

    logger.info("user registered", user_id=user["id"])
    return jsonify({"token": encode_token(user["id"]), "user": user}), 201


@bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""

    conn = connect_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT id, email, name, bio, avatar_url, role, created_at, password_hash
                   FROM users WHERE email = %s""",
                (email,),
            )
            row = cur.fetchone()
    finally:
        conn.close()

    if not row or not check_password_hash(row[7], password):
        return jsonify({"error": "неверный email или пароль"}), 401

    user = _user(row)
    logger.info("user logged in", user_id=user["id"])
    return jsonify({"token": encode_token(user["id"]), "user": user})


@bp.route("/me")
@require_auth
def me():
    conn = connect_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, email, name, bio, avatar_url, role, created_at FROM users WHERE id = %s",
                (g.current_user_id,),
            )
            row = cur.fetchone()
    finally:
        conn.close()

    if not row:
        return jsonify({"error": "пользователь не найден"}), 404

    return jsonify({"user": _user(row)})
