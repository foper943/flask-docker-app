import signal

from app import create_app
from config import Config

# gunicorn импортирует этот модуль как run:app — create_app() выполняется в воркере
app = create_app()


if __name__ == "__main__":
    # Обработчики сигналов только для dev-режима (python run.py).
    # При запуске через gunicorn сигналы обрабатывает app.worker.GracefulSyncWorker.
    def _handle_shutdown(signum, frame):
        from app import shutdown
        shutdown.set_shutting_down()
        # SystemExit запускает atexit-обработчики (логирование cleanup)
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, _handle_shutdown)
    signal.signal(signal.SIGINT, _handle_shutdown)

    app.run(
        host="0.0.0.0",
        port=Config.PORT,
        debug=Config.DEBUG,
        # reloader несовместим с обработчиками сигналов в __main__
        use_reloader=False,
    )
