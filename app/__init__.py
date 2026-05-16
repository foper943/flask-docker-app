import os

import structlog
from flask import Flask
from flask_cors import CORS

from .logging_config import configure_logging
from .middleware import register_middleware

logger = structlog.get_logger(__name__)


def create_app() -> Flask:
    service_name = os.getenv("SERVICE_NAME", "app")
    configure_logging(service_name)

    app = Flask(__name__)

    # CORS нужен для dev-режима (Vite на 5173 ↔ Flask на 5000)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    register_middleware(app)

    from .routes import main
    app.register_blueprint(main)

    from .blueprints.auth import bp as auth_bp
    from .blueprints.users import bp as users_bp
    from .blueprints.skills import bp as skills_bp
    from .blueprints.mentors import bp as mentors_bp
    from .blueprints.sessions import bp as sessions_bp
    from .blueprints.chat import bp as chat_bp
    from .blueprints.reviews import bp as reviews_bp
    from .blueprints.health import bp as health_bp

    for blueprint in (
        auth_bp, users_bp, skills_bp, mentors_bp,
        sessions_bp, chat_bp, reviews_bp, health_bp,
    ):
        app.register_blueprint(blueprint)

    # Инициализация WebSocket
    from .socket_events import socketio
    socketio.init_app(app)

    logger.info("приложение запущено")
    return app
