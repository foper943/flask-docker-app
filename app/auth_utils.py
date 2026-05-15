import os
from datetime import datetime, timezone, timedelta
from functools import wraps

import jwt
import structlog
from flask import g, jsonify, request

logger = structlog.get_logger(__name__)

_SECRET = os.getenv("SECRET_KEY", "dev-secret-change-in-production")
_ALG = "HS256"


def encode_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": user_id, "iat": now, "exp": now + timedelta(days=30)},
        _SECRET,
        algorithm=_ALG,
    )


def decode_token(token: str) -> int:
    payload = jwt.decode(token, _SECRET, algorithms=[_ALG])
    return int(payload["sub"])


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return jsonify({"error": "unauthorized"}), 401
        try:
            g.current_user_id = decode_token(header[7:])
        except jwt.InvalidTokenError as exc:
            logger.warning("invalid token", error=str(exc))
            return jsonify({"error": "invalid token"}), 401
        return f(*args, **kwargs)

    return decorated
