# Платформа взаимного обучения (Peer Learning Platform)

> Курсовая работа — финальная интеграция (12-factor app)

**Стек:** Flask · PostgreSQL · Redis · React/TypeScript · gunicorn · nginx · Docker Compose  
**Запуск:** `docker-compose up --build` → открыть **http://localhost:8080**

---

## Описание предметной области

Платформа взаимного обучения — это сервис, позволяющий людям обмениваться знаниями напрямую: один пользователь выступает ментором по навыку, другой — учеником.

### Роли пользователей

| Роль | Описание |
|------|----------|
| **learner** (ученик) | Ищет менторов, записывается на сессии, оставляет отзывы |
| **mentor** (ментор) | Предлагает свои навыки для обучения, принимает/подтверждает сессии |
| **both** | Совмещает обе роли — и учит, и учится |
| **admin** | Создаётся через CLI, управляет платформой |

### Бизнес-логика

- **Навыки** — каталог тем (Python, React, SQL, Docker, English и др.) с категориями
- **Менторы** — пользователи с хотя бы одним навыком типа `teaching`; видны в каталоге с рейтингом
- **Сессии** — ученик создаёт запрос к ментору по конкретному навыку → ментор подтверждает → после занятия отмечает `completed`
- **Отзывы** — оставить отзыв можно только после `completed`-сессии; участник сессии оценивает другого участника
- **Чат** — личные сообщения между пользователями в реальном времени через WebSocket

### Ключевые ограничения
- Нельзя записаться на сессию к самому себе
- Нельзя оставить отзыв без завершённой сессии
- Нельзя изменить чужой профиль

---

## Архитектура

UML-диаграммы (Use Case, ER, Sequence, Component) — в файле [`docs/architecture.md`](docs/architecture.md).

```
Браузер
   │
   ▼
nginx:8080
   ├── /socket.io/ ──► Flask (WebSocket)
   ├── /api/       ──► Flask (REST API)
   ├── /health     ──► Flask
   └── /*          ──► React SPA (собранный Vite)

Flask
   ├── psycopg2 ──► PostgreSQL (данные)
   └── redis-py ──► Redis (кэш, счётчики, pub/sub)
```

---

## Деплой

> Задеплоить можно на [Render.com](https://render.com) через готовый `render.yaml`:
> 1. Fork репозитория на GitHub
> 2. На Render: New → Blueprint → выбрать репозиторий
> 3. Render автоматически создаст PostgreSQL, Redis и запустит приложение

Конфиг деплоя: [`render.yaml`](render.yaml)

---

## Шаг 1. Унификация окружений

### Что сделано

В `docker-compose.yml` все зависимости запускаются в контейнерах с **зафиксированными версиями образов** — никаких `:latest`.

| Сервис     | Образ               | Роль                  |
|------------|---------------------|-----------------------|
| app        | python:3.12-slim    | Flask-приложение      |
| db         | postgres:16.2       | Основная БД           |
| redis      | redis:7.2.4         | Кэш / счётчики        |
| nginx      | nginx:1.27.0        | Реверс-прокси         |
| frontend   | node:20-alpine      | Сборка React SPA      |

Приложение **не стартует** пока БД не пройдёт healthcheck (`pg_isready`), а Redis не ответит на `PING`. Это исключает ситуацию «сервис поднялся, но база ещё не готова».

```yaml
# docker-compose.yml (фрагмент)
depends_on:
  db:
    condition: service_healthy
  redis:
    condition: service_healthy

healthcheck:          # для сервиса db
  test: ["CMD-SHELL", "pg_isready -U postgres"]
  interval: 10s
  timeout: 5s
  retries: 5
```

### Как проверить

```bash
docker-compose ps
# Все сервисы должны показывать статус "healthy"
```

---

## Шаг 2. Быстрый старт

### Что сделано

**Dockerfile** оптимизирован по трём направлениям:

1. **Лёгкий базовый образ** — `python:3.12-slim` вместо `python:3.12`  
   (размер ~50 МБ против ~900 МБ у full-образа)

2. **Правильный порядок слоёв** — зависимости копируются и устанавливаются  
   *до* копирования кода. При изменении только кода Docker берёт слой  
   с `pip install` из кэша — пересборка занимает секунды.

```dockerfile
# Dockerfile
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .          # ← сначала зависимости
RUN pip install --no-cache-dir -r requirements.txt

COPY . .                         # ← потом код

HEALTHCHECK --interval=10s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

CMD ["gunicorn", "--config", "gunicorn.conf.py", "run:app"]
```

3. **gunicorn вместо Flask dev-сервера** — production-ready WSGI-сервер  
   с `preload_app = True` (приложение загружается один раз в мастер-процессе).

### Как проверить

```bash
# Время от старта до первого ответа
time curl http://localhost:8080/api/skills
# Ожидаемо: < 2 секунд после подъёма контейнера
```

---

## Шаг 3. Обработка сигналов завершения

### Что сделано

Реализован многоуровневый graceful shutdown:

**`app/shutdown.py`** — глобальный флаг и логирование событий:
```python
is_shutting_down = False

def set_shutting_down() -> None:
    global is_shutting_down
    is_shutting_down = True
    logger.info("received SIGTERM")
    logger.info("waiting for requests to complete")

def _on_exit() -> None:          # вызывается через atexit при выходе процесса
    structlog.contextvars.clear_contextvars()
    logger.info("closing DB connections")
    logger.info("shutdown complete")

atexit.register(_on_exit)
```

**`app/worker.py`** — кастомный gunicorn worker, перехватывает сигналы:
```python
class GracefulSyncWorker(SyncWorker):
    def handle_quit(self, sig, frame):   # SIGQUIT — штатное завершение
        from app import shutdown
        shutdown.set_shutting_down()
        super().handle_quit(sig, frame)  # gunicorn ждёт текущий запрос

    def handle_exit(self, sig, frame):   # SIGTERM напрямую на воркер
        from app import shutdown
        shutdown.set_shutting_down()
        super().handle_exit(sig, frame)
```

**`gunicorn.conf.py`** — таймаут штатного завершения 30 секунд:
```python
graceful_timeout = 30
worker_class = "app.worker.GracefulSyncWorker"
```

**`docker-compose.yml`** — Docker ждёт дольше таймаута приложения:
```yaml
stop_grace_period: 35s   # > graceful_timeout (30s)
```

**`run.py`** — обработка сигналов для dev-режима (`python run.py`):
```python
def _handle_shutdown(signum, frame):
    from app import shutdown
    shutdown.set_shutting_down()
    raise SystemExit(0)           # запускает atexit-обработчики

signal.signal(signal.SIGTERM, _handle_shutdown)
signal.signal(signal.SIGINT, _handle_shutdown)
```

---

## Шаг 4. Тестирование graceful shutdown

### Демонстрация

**Терминал 1** — запускаем и смотрим логи:
```bash
docker-compose up -d
docker-compose logs -f app
```

**Терминал 2** — отправляем SIGTERM:
```bash
docker kill --signal=SIGTERM pr_1-app-1
```

**Ожидаемые логи** (в строгом порядке):
```json
{"message": "received SIGTERM", "level": "info", ...}
{"message": "waiting for requests to complete", "level": "info", ...}
{"message": "closing DB connections", "level": "info", ...}
{"message": "shutdown complete", "level": "info", ...}
```

**Проверка кода выхода** (должен быть `0`):
```bash
docker inspect pr_1-app-1 --format='{{.State.ExitCode}}'
# → 0
```

### Проверка отказа новым запросам во время shutdown

В `app/middleware.py` добавлен middleware, который при `is_shutting_down = True`  
возвращает `503 Service Unavailable` с заголовком `Retry-After: 10`:

```python
@app.before_request
def _check_shutdown():
    from app import shutdown
    if shutdown.is_shutting_down:
        return jsonify({"error": "service unavailable"}), 503, {"Retry-After": "10"}
```

**Проверка:**
```bash
# В одном терминале — непрерывно шлём запросы
while true; do curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8080/; sleep 0.5; done

# В другом — посылаем SIGTERM
docker kill --signal=SIGTERM pr_1-app-1
```

Уже начавшиеся запросы вернут **200**, новые во время shutdown — **503**.

---

## Шаг 5. Утилизируемость

### Почему данные не теряются

Приложение не хранит состояние в памяти:

| Данные         | Где хранятся          | Переживает перезапуск |
|----------------|------------------------|----------------------|
| Сообщения      | PostgreSQL (volume)    | ✅ да                |
| Счётчики       | Redis                  | ✅ да (AOF/RDB)      |
| Сессия юзера   | JWT в браузере         | ✅ да                |
| In-flight HTTP | gunicorn graceful stop | ✅ завершаются       |

### Демонстрация устойчивости

```bash
# Запускаем нагрузку
while true; do curl -s http://localhost:8080/api/skills > /dev/null; done &

# Убиваем контейнер
docker-compose restart app

# Нагрузка продолжает работать — nginx буферизует, потерь нет
```

---

## Структура проекта

```
├── app/
│   ├── __init__.py          # create_app(), регистрация blueprint'ов
│   ├── auth_utils.py        # JWT: encode/decode, @require_auth
│   ├── db.py                # connect_db()
│   ├── db_init.py           # CREATE TABLE IF NOT EXISTS для всех таблиц
│   ├── shutdown.py          # флаг is_shutting_down, atexit-cleanup
│   ├── worker.py            # GracefulSyncWorker (перехват SIGQUIT/SIGTERM)
│   ├── middleware.py        # request_id трассировка + 503 при shutdown
│   ├── logging_config.py    # structlog JSON → stdout/stderr
│   ├── routes.py            # демо-маршруты (/, /messages, /counter)
│   ├── blueprints/          # API маршруты (/api/auth, /users, /skills, ...)
│   └── repositories/        # слой доступа к данным (psycopg2)
├── frontend/                # React 18 + TypeScript + Tailwind (Vite)
├── gunicorn.conf.py         # workers=2, graceful_timeout=30, preload_app=True
├── run.py                   # точка входа, signal handlers для dev-режима
├── Dockerfile               # python:3.12-slim, multi-layer cache
├── docker-compose.yml       # все сервисы с healthcheck и stop_grace_period
└── nginx.conf               # /api/* → Flask, /* → React SPA
```

---

## Быстрый старт для проверки

```bash
# 1. Клонировать и запустить (миграции применяются автоматически)
git clone <repo>
cd pr_1
docker-compose up --build

# 2. Открыть браузер
open http://localhost:8080

# 3. Зарегистрироваться и попробовать приложение

# 4. Протестировать graceful shutdown
docker kill --signal=SIGTERM pr_1-app-1
docker-compose logs app | tail -20
docker inspect pr_1-app-1 --format='{{.State.ExitCode}}'
```

---

## Административные команды

Все команды работают как внутри контейнера, так и через `docker run --rm`.

### Применение миграций

```bash
# Локально
python cli.py migrate

# Через Docker (без входа в контейнер)
docker run --rm \
  -e DATABASE_URL=postgresql://postgres:postgres@db:5432/mydb \
  -e REDIS_URL=redis://redis:6379/0 \
  myapp:latest python cli.py migrate
```

### Создание администратора

```bash
# Локально
python cli.py create-admin --email=admin@example.com --password=secret

# Через Docker (без входа в контейнер)
docker run --rm \
  -e DATABASE_URL=postgresql://postgres:postgres@db:5432/mydb \
  -e REDIS_URL=redis://redis:6379/0 \
  myapp:latest python cli.py create-admin \
    --email=admin@example.com --password=secret
```

### Очистка Redis-кэша

```bash
# Локально
python cli.py clear-cache

# Через Docker (без входа в контейнер)
docker run --rm \
  -e REDIS_URL=redis://redis:6379/0 \
  myapp:latest python cli.py clear-cache
```

### Запуск сервера

```bash
# Напрямую (использует gunicorn внутри)
python cli.py server

# Или через docker-compose (основной способ)
docker-compose up
```

### Проверка здоровья сервиса

```bash
curl http://localhost:8080/health
# Ответ при всё работает:
# {"status":"ok","service":"app","version":"dev","checks":{"database":"ok","redis":"ok"}}
```

---

## Структура миграций

Миграции хранятся в каталоге `migrations/` в виде пронумерованных SQL-файлов.
Применённые миграции трекаются в таблице `schema_migrations` в БД.
Повторный запуск `python cli.py migrate` безопасен — уже применённые миграции пропускаются.

```
migrations/
├── 001_initial_schema.sql   # все таблицы платформы
└── 002_seed_skills.sql      # начальные данные (навыки)
```

Чтобы добавить новую миграцию — создайте файл с следующим номером (например `003_add_index.sql`).

---

## CI/CD пайплайн (GitHub Actions)

Файл: `.github/workflows/deploy.yml`

| Шаг | Триггер | Действие |
|-----|---------|----------|
| **build** | push в main | Сборка образа → пуш в `ghcr.io` с тегами `latest` и `sha-<commit>` |
| **migrate** | после build | `docker run python cli.py migrate` — при ошибке деплой останавливается |
| **deploy** | после migrate | SSH → `docker-compose pull && up -d` на staging-сервере |
| **healthcheck** | после deploy | `curl --retry 5` на `/health`, проверяет что сервис отвечает 200 |
| **rollback** | `workflow_dispatch` | Откат на тег образа из параметра `image_tag` |

**Необходимые GitHub Secrets:**

| Секрет | Описание |
|--------|----------|
| `DATABASE_URL` | URL PostgreSQL на staging |
| `REDIS_URL` | URL Redis на staging |
| `STAGING_HOST` | IP/hostname staging-сервера |
| `STAGING_USER` | SSH-пользователь |
| `STAGING_SSH_KEY` | Приватный SSH-ключ |

---

## 12-factor checklist

| # | Фактор | Реализация в проекте |
|---|--------|----------------------|
| I | **Codebase** — один репозиторий | Один Git-репозиторий, несколько окружений (dev / staging / prod) через env-переменные |
| II | **Dependencies** — явные зависимости | `requirements.txt` (Python) и `package.json` (Node) — все зависимости зафиксированы |
| III | **Config** — конфиг через env | Все параметры (`DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, `PORT`) берутся из env; хардкода нет |
| IV | **Backing services** — сервисы как ресурсы | БД и Redis подключаются через URL из env; замена на внешний сервис — только смена переменной |
| V | **Build / release / run** — разделение этапов | CI собирает образ (build) → `python cli.py migrate` применяет схему (release) → `docker-compose up` запускает (run) |
| VI | **Processes** — stateless-процессы | Контейнеры не хранят состояние в памяти; всё персистентное — в PostgreSQL и Redis |
| VII | **Port binding** — приложение само слушает порт | Flask/gunicorn слушает `$PORT`; nginx проксирует снаружи |
| VIII | **Concurrency** — масштабирование процессами | `replicas` в docker-compose; gunicorn запускает несколько воркеров |
| IX | **Disposability** — быстрый старт и graceful shutdown | `GracefulSyncWorker` + `stop_grace_period: 35s`; старт < 2 сек (preload_app) |
| X | **Dev/prod parity** — одинаковые среды | Одни и те же Docker-образы с зафиксированными тегами в dev и prod |
| XI | **Logs** — логи как поток событий | structlog JSON → stdout/stderr; агрегация на стороне платформы |
| XII | **Admin processes** — одноразовые задачи | `python cli.py migrate` / `create-admin` / `clear-cache` — запускаются как отдельные контейнеры |
