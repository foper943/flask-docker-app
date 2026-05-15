from gunicorn.workers.sync import SyncWorker


class GracefulSyncWorker(SyncWorker):
    """Gunicorn worker, выставляющий флаг is_shutting_down до начала штатного завершения.

    handle_quit  — вызывается при SIGQUIT (graceful stop от мастера)
    handle_exit  — вызывается при SIGTERM напрямую на воркер
    """

    def handle_quit(self, sig, frame):
        from app import shutdown
        shutdown.set_shutting_down()
        super().handle_quit(sig, frame)

    def handle_exit(self, sig, frame):
        from app import shutdown
        shutdown.set_shutting_down()
        super().handle_exit(sig, frame)
