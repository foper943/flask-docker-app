# Flask Microservice

Микросервис на Flask + PostgreSQL + Redis, запускаемый через Docker Compose.

## Запуск

```bash
docker-compose up --build
```

## Маршруты

| Метод | Путь        | Описание                          |
|-------|-------------|-----------------------------------|
| GET   | `/`         | Добавить и вернуть последнее сообщение |
| GET   | `/messages` | Список всех сообщений             |
| POST  | `/messages` | Создать сообщение `{"text": "..."}` |
| GET   | `/counter`  | Инкрементировать счётчик Redis    |

## Логирование

Все логи выводятся в **JSON-формате** строго в stdout/stderr:

- `INFO`, `WARNING` → stdout
- `ERROR`, `CRITICAL` → stderr

Docker автоматически подхватывает оба потока через драйвер `json-file`.

### Просмотр логов

```bash
docker-compose logs -f app
```

### Пример вывода

```json
{"service": "app", "request_id": "a1b2c3d4-...", "method": "GET", "path": "/messages", "status_code": 200, "level": "info", "timestamp": "2025-05-08T12:00:00.000000Z", "message": "request handled"}
```

### Поля каждой записи

| Поле          | Описание                                    |
|---------------|---------------------------------------------|
| `level`       | Уровень: `info` / `warning` / `error`       |
| `timestamp`   | ISO 8601, UTC                               |
| `service`     | Имя сервиса (переменная `SERVICE_NAME`)     |
| `request_id`  | UUID из заголовка `X-Request-ID` или новый |
| `method`      | HTTP-метод запроса                          |
| `path`        | URL-путь                                    |
| `status_code` | HTTP-статус ответа                          |
| `message`     | Описание события                            |

### Сквозная трассировка Request ID

Каждый входящий запрос получает уникальный `request_id`:

1. Читается из заголовка `X-Request-ID`, если передан клиентом.
2. Иначе генерируется новый UUID.
3. Возвращается в заголовке ответа `X-Request-ID`.
4. Автоматически добавляется во все логи внутри обработки запроса.

## Запуск фронтенда

### Через Docker Compose (рекомендуется)

```bash
docker-compose up --build
# Открыть: http://localhost:8080
```

Nginx на порту 8080 маршрутизирует:
- `/api/*` → Flask :5000
- `/*` → React SPA :3000

### Локальная разработка (без Docker)

```bash
cd frontend
npm install
npm run dev
# Открыть: http://localhost:5173
# Vite автоматически проксирует /api → http://localhost:5000
```

### Сборка без Docker

```bash
cd frontend
npm install
npm run build        # dist/
npm run preview      # preview на порту 3000
```

## Тестирование graceful shutdown

```bash
# Запуск
docker-compose up -d

# Отправить SIGTERM конкретному контейнеру
docker kill --signal=SIGTERM <container_name>

# Наблюдать логи завершения
docker-compose logs -f app
```

В логах должна появиться следующая последовательность:

```json
{"message": "received SIGTERM", ...}
{"message": "waiting for requests to complete", ...}
{"message": "closing DB connections", ...}
{"message": "shutdown complete", ...}
```

Код выхода контейнера должен быть `0`:

```bash
docker inspect <container_name> --format='{{.State.ExitCode}}'
```

Чтобы убедиться, что in-flight запросы завершились успешно, можно запустить
длинный запрос и одновременно отправить SIGTERM — ответ должен прийти с кодом 200,
а новые запросы во время shutdown получат `503 Service Unavailable` с заголовком
`Retry-After: 10`.

## Структура слоёв

```
routers (routes.py)
  └── services (services.py)       ← бизнес-логика
        └── repositories/          ← только SQL / Redis
              ├── base.py          (ABC-интерфейсы)
              ├── message_repository.py
              └── counter_repository.py
```
