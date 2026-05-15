import atexit

import structlog

logger = structlog.get_logger(__name__)

is_shutting_down = False


def set_shutting_down() -> None:
    global is_shutting_down
    if is_shutting_down:
        return
    is_shutting_down = True
    logger.info("received SIGTERM")
    logger.info("waiting for requests to complete")


def _on_exit() -> None:
    if not is_shutting_down:
        return
    # Очищаем контекст запроса — на этом этапе активного запроса нет
    structlog.contextvars.clear_contextvars()
    logger.info("closing DB connections")
    logger.info("shutdown complete")


atexit.register(_on_exit)
