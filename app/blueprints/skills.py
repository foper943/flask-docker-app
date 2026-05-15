import structlog
from flask import Blueprint, g, jsonify, request

from app.auth_utils import require_auth
from app.db import connect_db

logger = structlog.get_logger(__name__)
bp = Blueprint("skills", __name__, url_prefix="/api/skills")


def _skill(row) -> dict:
    return {
        "id": row[0],
        "name": row[1],
        "category": row[2],
        "description": row[3],
        "mentor_count": row[4],
        "created_at": row[5].isoformat() if row[5] else None,
    }


@bp.route("")
def list_skills():
    search = (request.args.get("search") or "").strip()
    category = (request.args.get("category") or "").strip()

    conn = connect_db()
    try:
        with conn.cursor() as cur:
            query = """
                SELECT s.id, s.name, s.category, s.description,
                       COUNT(DISTINCT us.user_id) AS mentor_count,
                       s.created_at
                FROM skills s
                LEFT JOIN user_skills us ON us.skill_id = s.id AND us.type = 'teaching'
                WHERE (%s = '' OR s.name ILIKE '%%' || %s || '%%')
                  AND (%s = '' OR s.category = %s)
                GROUP BY s.id
                ORDER BY mentor_count DESC, s.name
            """
            cur.execute(query, (search, search, category, category))
            skills = [_skill(r) for r in cur.fetchall()]

            cur.execute("SELECT DISTINCT category FROM skills ORDER BY category")
            categories = [r[0] for r in cur.fetchall()]
    finally:
        conn.close()

    return jsonify({"skills": skills, "categories": categories})


@bp.route("/<int:skill_id>")
def get_skill(skill_id: int):
    conn = connect_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT s.id, s.name, s.category, s.description,
                          COUNT(DISTINCT us.user_id) AS mentor_count,
                          s.created_at
                   FROM skills s
                   LEFT JOIN user_skills us ON us.skill_id = s.id AND us.type = 'teaching'
                   WHERE s.id = %s
                   GROUP BY s.id""",
                (skill_id,),
            )
            row = cur.fetchone()
            if not row:
                return jsonify({"error": "навык не найден"}), 404
            skill = _skill(row)

            cur.execute(
                """SELECT u.id, u.name, u.bio, u.avatar_url, u.role,
                          COALESCE(AVG(r.rating), 0) AS avg_rating,
                          COUNT(r.id) AS review_count
                   FROM users u
                   JOIN user_skills us ON us.user_id = u.id AND us.skill_id = %s AND us.type = 'teaching'
                   LEFT JOIN reviews r ON r.reviewee_id = u.id
                   GROUP BY u.id
                   ORDER BY avg_rating DESC""",
                (skill_id,),
            )
            mentors = [
                {
                    "id": r[0], "name": r[1], "bio": r[2],
                    "avatar_url": r[3], "role": r[4],
                    "average_rating": float(r[5]) if r[5] else None,
                    "review_count": r[6],
                }
                for r in cur.fetchall()
            ]
    finally:
        conn.close()

    return jsonify({"skill": skill, "mentors": mentors})


@bp.route("", methods=["POST"])
@require_auth
def create_skill():
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    category = (data.get("category") or "").strip()
    description = data.get("description")

    if not name or not category:
        return jsonify({"error": "name и category обязательны"}), 400

    conn = connect_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO skills (name, category, description) VALUES (%s, %s, %s)
                   ON CONFLICT (name) DO NOTHING
                   RETURNING id, name, category, description, 0, created_at""",
                (name, category, description),
            )
            row = cur.fetchone()
            if not row:
                return jsonify({"error": "навык с таким именем уже существует"}), 409
            skill = _skill(row)
        conn.commit()
    finally:
        conn.close()

    return jsonify({"skill": skill}), 201
