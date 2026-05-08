import logging
import sys

import structlog


class _StdoutFilter(logging.Filter):
    """Passes only records below ERROR level (INFO, WARNING → stdout)."""

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno < logging.ERROR


def configure_logging(service_name: str) -> None:
    """Set up structlog with JSON output: INFO/WARNING → stdout, ERROR+ → stderr."""

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.DEBUG)
    stdout_handler.addFilter(_StdoutFilter())

    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.ERROR)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.handlers = []
    root.addHandler(stdout_handler)
    root.addHandler(stderr_handler)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.EventRenamer("message"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Bind service name globally so every log record carries it.
    structlog.contextvars.bind_contextvars(service=service_name)
