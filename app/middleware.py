import uuid

import structlog
from flask import Flask, g, jsonify, request

logger = structlog.get_logger(__name__)


def register_middleware(app: Flask) -> None:
    """Регистрирует middleware: трассировка request_id, shutdown-проверка, access-лог."""

    @app.before_request
    def _bind_request_context() -> None:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        g.request_id = request_id
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.path,
        )

    @app.before_request
    def _check_shutdown():
        # Импорт ленивый — shutdown.py загружается при первом запросе после регистрации
        from app import shutdown
        if shutdown.is_shutting_down:
            return (
                jsonify({"error": "service unavailable"}),
                503,
                {"Retry-After": "10"},
            )

    @app.after_request
    def _log_and_tag_response(response):
        structlog.contextvars.bind_contextvars(status_code=response.status_code)
        logger.info("request handled")
        response.headers["X-Request-ID"] = g.get("request_id", "")
        return response
