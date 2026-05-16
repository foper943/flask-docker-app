import signal
import sys

from app import create_app
from app.socket_events import socketio
from config import Config

app = create_app()


if __name__ == "__main__":
    def _handle_shutdown(signum, frame):
        from app import shutdown
        shutdown.set_shutting_down()
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, _handle_shutdown)
    signal.signal(signal.SIGINT, _handle_shutdown)

    # В dev-режиме запускаем через socketio.run для поддержки WebSocket
    socketio.run(
        app,
        host="0.0.0.0",
        port=Config.PORT,
        debug=Config.DEBUG,
        use_reloader=False,
    )
