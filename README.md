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

## Структура слоёв

```
routers (routes.py)
  └── services (services.py)       ← бизнес-логика
        └── repositories/          ← только SQL / Redis
              ├── base.py          (ABC-интерфейсы)
              ├── message_repository.py
              └── counter_repository.py
```
