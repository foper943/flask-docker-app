import os

import structlog
from flask import Flask

from .logging_config import configure_logging
from .middleware import register_middleware

logger = structlog.get_logger(__name__)


def create_app() -> Flask:
    service_name = os.getenv("SERVICE_NAME", "app")
    configure_logging(service_name)

    app = Flask(__name__)

    register_middleware(app)

    from .routes import main
    app.register_blueprint(main)

    # Ensure DB schema exists before serving any traffic.
    from .repositories.message_repository import MessageRepository
    MessageRepository().ensure_table()
    logger.info("application started")

    return app
