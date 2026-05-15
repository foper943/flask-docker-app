bind = "0.0.0.0:5000"
workers = 2

# timeout — максимальное время обработки одного запроса (убивает зависший воркер)
timeout = 30

# graceful_timeout — сколько ждать воркера при штатном завершении
graceful_timeout = 30

# кастомный worker перехватывает SIGQUIT и выставляет флаг is_shutting_down
worker_class = "app.worker.GracefulSyncWorker"

accesslog = "-"
errorlog = "-"
loglevel = "warning"
