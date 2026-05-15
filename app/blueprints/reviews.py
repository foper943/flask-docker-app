import structlog
from flask import Blueprint, g, jsonify, request

from app.auth_utils import require_auth
from app.db import connect_db

logger = structlog.get_logger(__name__)
bp = Blueprint("reviews", __name__, url_prefix="/api/reviews")


@bp.route("/<int:user_id>")
def get_reviews(user_id: int):
    conn = connect_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT rv.id, rv.reviewer_id, u.name, u.avatar_url,
                          rv.reviewee_id, rv.session_id, rv.rating, rv.comment, rv.created_at
                   FROM reviews rv
                   JOIN users u ON u.id = rv.reviewer_id
                   WHERE rv.reviewee_id = %s
                   ORDER BY rv.created_at DESC""",
                (user_id,),
            )
            reviews = [
                {
                    "id": r[0], "reviewer_id": r[1], "reviewer_name": r[2],
                    "reviewer_avatar": r[3], "reviewee_id": r[4], "session_id": r[5],
                    "rating": r[6], "comment": r[7],
                    "created_at": r[8].isoformat() if r[8] else None,
                }
                for r in cur.fetchall()
            ]

            cur.execute(
                "SELECT AVG(rating), COUNT(*) FROM reviews WHERE reviewee_id = %s", (user_id,)
            )
            agg = cur.fetchone()
    finally:
        conn.close()

    avg = round(float(agg[0]), 2) if agg[0] else None
    return jsonify({"reviews": reviews, "average_rating": avg, "count": agg[1]})


@bp.route("", methods=["POST"])
@require_auth
def create_review():
    data = request.get_json() or {}
    reviewee_id = data.get("reviewee_id")
    session_id = data.get("session_id")
    rating = data.get("rating")
    comment = data.get("comment")

    if not all([reviewee_id, session_id, rating]):
        return jsonify({"error": "reviewee_id, session_id и rating обязательны"}), 400
    if not isinstance(rating, int) or not (1 <= rating <= 5):
        return jsonify({"error": "rating должен быть целым числом от 1 до 5"}), 400

    conn = connect_db()
    try:
        with conn.cursor() as cur:
            # Проверяем, что сессия завершена и автор — её участник
            cur.execute(
                "SELECT status, mentor_id, learner_id FROM sessions WHERE id = %s", (session_id,)
            )
            row = cur.fetchone()
            if not row:
                return jsonify({"error": "сессия не найдена"}), 404
            if row[0] != "completed":
                return jsonify({"error": "отзыв можно оставить только после завершённой сессии"}), 422
            if g.current_user_id not in (row[1], row[2]):
                return jsonify({"error": "вы не участвовали в этой сессии"}), 403

            cur.execute(
                """INSERT INTO reviews (reviewer_id, reviewee_id, session_id, rating, comment)
                   VALUES (%s, %s, %s, %s, %s)
                   RETURNING id, reviewer_id, reviewee_id, session_id, rating, comment, created_at""",
                (g.current_user_id, reviewee_id, session_id, rating, comment),
            )
            r = cur.fetchone()
            review = {
                "id": r[0], "reviewer_id": r[1], "reviewee_id": r[2],
                "session_id": r[3], "rating": r[4], "comment": r[5],
                "created_at": r[6].isoformat() if r[6] else None,
            }
        conn.commit()
    finally:
        conn.close()

    return jsonify({"review": review}), 201
