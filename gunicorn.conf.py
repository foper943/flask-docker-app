bind = "0.0.0.0:5000"
workers = 2

# gevent нужен для WebSocket (Flask-SocketIO)
worker_class = "gevent"
worker_connections = 1000

# timeout — максимальное время обработки одного запроса
timeout = 30

# graceful_timeout — сколько ждать воркера при штатном завершении
graceful_timeout = 30

accesslog = "-"
errorlog = "-"
loglevel = "warning"

# Загружаем приложение один раз в мастер-процессе до fork воркеров
preload_app = True
