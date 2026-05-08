import uuid

import structlog
from flask import Flask, g, request

logger = structlog.get_logger(__name__)


def register_middleware(app: Flask) -> None:
    """Register request-ID tracing and per-request access logging."""

    @app.before_request
    def _bind_request_context() -> None:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        g.request_id = request_id
        # Clear any context left from a previous request on this thread,
        # then bind fresh values so every log line in this request carries them.
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.path,
        )

    @app.after_request
    def _log_and_tag_response(response):
        structlog.contextvars.bind_contextvars(status_code=response.status_code)
        logger.info("request handled")
        response.headers["X-Request-ID"] = g.get("request_id", "")
        return response
