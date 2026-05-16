import os

import structlog
from flask import Blueprint, jsonify

from app.db import connect_db, connect_redis

logger = structlog.get_logger(__name__)
bp = Blueprint("health", __name__)


@bp.route("/health")
def health():
    checks = {}

    # Проверка базы данных
    try:
        conn = connect_db()
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
        conn.close()
        checks["database"] = "ok"
    except Exception as exc:
        logger.error("health: БД недоступна", error=str(exc))
        checks["database"] = "error"

    # Проверка Redis
    try:
        r = connect_redis()
        r.ping()
        checks["redis"] = "ok"
    except Exception as exc:
        logger.error("health: Redis недоступен", error=str(exc))
        checks["redis"] = "error"

    all_ok = all(v == "ok" for v in checks.values())
    status_code = 200 if all_ok else 503

    return (
        jsonify(
            {
                "status": "ok" if all_ok else "error",
                "service": os.getenv("SERVICE_NAME", "peer-learn"),
                "version": os.getenv("APP_VERSION", "unknown"),
                "checks": checks,
            }
        ),
        status_code,
    )
