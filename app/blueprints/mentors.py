import structlog
from flask import Blueprint, jsonify, request

from app.db import connect_db

logger = structlog.get_logger(__name__)
bp = Blueprint("mentors", __name__, url_prefix="/api/mentors")


@bp.route("")
def list_mentors():
    skill_id = request.args.get("skill_id", type=int)
    min_rating = request.args.get("min_rating", type=float, default=0)

    conn = connect_db()
    try:
        with conn.cursor() as cur:
            query = """
                SELECT u.id, u.name, u.bio, u.avatar_url, u.role,
                       COALESCE(AVG(r.rating), 0) AS avg_rating,
                       COUNT(DISTINCT r.id) AS review_count
                FROM users u
                JOIN user_skills us ON us.user_id = u.id AND us.type = 'teaching'
                LEFT JOIN reviews r ON r.reviewee_id = u.id
                WHERE (%s IS NULL OR us.skill_id = %s)
                GROUP BY u.id
                HAVING COALESCE(AVG(r.rating), 0) >= %s
                ORDER BY avg_rating DESC, u.name
            """
            cur.execute(query, (skill_id, skill_id, min_rating))
            rows = cur.fetchall()

            mentor_ids = [r[0] for r in rows]
            skills_map: dict[int, list] = {mid: [] for mid in mentor_ids}

            if mentor_ids:
                cur.execute(
                    """SELECT us.user_id, us.skill_id, s.name, s.category, us.type
                       FROM user_skills us
                       JOIN skills s ON s.id = us.skill_id
                       WHERE us.user_id = ANY(%s) AND us.type = 'teaching'""",
                    (mentor_ids,),
                )
                for sr in cur.fetchall():
                    skills_map[sr[0]].append(
                        {"skill_id": sr[1], "skill_name": sr[2], "skill_category": sr[3], "type": sr[4]}
                    )

        mentors = [
            {
                "id": r[0], "name": r[1], "bio": r[2], "avatar_url": r[3], "role": r[4],
                "average_rating": round(float(r[5]), 2) if r[5] else None,
                "review_count": r[6],
                "skills": skills_map[r[0]],
            }
            for r in rows
        ]
    finally:
        conn.close()

    return jsonify({"mentors": mentors})


@bp.route("/<int:mentor_id>")
def get_mentor(mentor_id: int):
    conn = connect_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT u.id, u.name, u.bio, u.avatar_url, u.role,
                          COALESCE(AVG(r.rating), 0) AS avg_rating,
                          COUNT(DISTINCT r.id) AS review_count
                   FROM users u
                   LEFT JOIN reviews r ON r.reviewee_id = u.id
                   WHERE u.id = %s
                   GROUP BY u.id""",
                (mentor_id,),
            )
            row = cur.fetchone()
            if not row:
                return jsonify({"error": "ментор не найден"}), 404

            mentor = {
                "id": row[0], "name": row[1], "bio": row[2], "avatar_url": row[3], "role": row[4],
                "average_rating": round(float(row[5]), 2) if row[5] else None,
                "review_count": row[6],
            }

            cur.execute(
                """SELECT us.skill_id, s.name, s.category, us.type
                   FROM user_skills us JOIN skills s ON s.id = us.skill_id
                   WHERE us.user_id = %s""",
                (mentor_id,),
            )
            mentor["skills"] = [
                {"skill_id": r[0], "skill_name": r[1], "skill_category": r[2], "type": r[3]}
                for r in cur.fetchall()
            ]

            cur.execute(
                """SELECT rv.id, rv.reviewer_id, u.name, u.avatar_url,
                          rv.session_id, rv.rating, rv.comment, rv.created_at
                   FROM reviews rv
                   JOIN users u ON u.id = rv.reviewer_id
                   WHERE rv.reviewee_id = %s
                   ORDER BY rv.created_at DESC""",
                (mentor_id,),
            )
            mentor["reviews"] = [
                {
                    "id": r[0], "reviewer_id": r[1], "reviewer_name": r[2],
                    "reviewer_avatar": r[3], "session_id": r[4],
                    "rating": r[5], "comment": r[6],
                    "created_at": r[7].isoformat() if r[7] else None,
                }
                for r in cur.fetchall()
            ]
    finally:
        conn.close()

    return jsonify({"mentor": mentor})
