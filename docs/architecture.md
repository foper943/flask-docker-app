# Архитектура платформы взаимного обучения

## Use Case диаграмма

```mermaid
flowchart TD
    Гость([Гость])
    Ученик([Ученик])
    Ментор([Ментор])
    Админ([Администратор])

    subgraph Аутентификация
        UC1[Зарегистрироваться]
        UC2[Войти в систему]
        UC3[Выйти из системы]
    end

    subgraph Профиль
        UC4[Просмотреть профиль]
        UC5[Редактировать профиль]
        UC6[Выбрать навыки для обучения]
        UC7[Выбрать навыки для преподавания]
    end

    subgraph Навыки и менторы
        UC8[Просмотреть каталог навыков]
        UC9[Найти менторов по навыку]
        UC10[Просмотреть профиль ментора]
    end

    subgraph Сессии
        UC11[Записаться на сессию]
        UC12[Подтвердить запрос на сессию]
        UC13[Отметить сессию завершённой]
        UC14[Отменить сессию]
        UC15[Просмотреть свои сессии]
    end

    subgraph Отзывы
        UC16[Оставить отзыв после сессии]
        UC17[Просмотреть отзывы о менторе]
    end

    subgraph Чат
        UC18[Написать сообщение]
        UC19[Получить сообщения в реальном времени]
        UC20[Просмотреть историю диалогов]
    end

    subgraph Администрирование
        UC21[Создать администратора через CLI]
        UC22[Применить миграции через CLI]
        UC23[Очистить кэш через CLI]
    end

    Гость --> UC1
    Гость --> UC2

    Ученик --> UC3
    Ученик --> UC4
    Ученик --> UC5
    Ученик --> UC6
    Ученик --> UC8
    Ученик --> UC9
    Ученик --> UC10
    Ученик --> UC11
    Ученик --> UC15
    Ученик --> UC16
    Ученик --> UC17
    Ученик --> UC18
    Ученик --> UC19
    Ученик --> UC20

    Ментор --> UC7
    Ментор --> UC12
    Ментор --> UC13
    Ментор --> UC14

    Админ --> UC21
    Админ --> UC22
    Админ --> UC23
```

---

## ER-диаграмма базы данных

```mermaid
erDiagram
    users {
        serial id PK
        text email UK
        text password_hash
        text name
        text bio
        text avatar_url
        text role
        timestamptz created_at
    }

    skills {
        serial id PK
        text name UK
        text category
        text description
        timestamptz created_at
    }

    user_skills {
        serial id PK
        integer user_id FK
        integer skill_id FK
        text type
    }

    sessions {
        serial id PK
        integer mentor_id FK
        integer learner_id FK
        integer skill_id FK
        text status
        timestamptz scheduled_at
        text topic
        timestamptz created_at
    }

    chat_messages {
        serial id PK
        integer sender_id FK
        integer receiver_id FK
        text text
        boolean is_read
        timestamptz created_at
    }

    reviews {
        serial id PK
        integer reviewer_id FK
        integer reviewee_id FK
        integer session_id FK
        integer rating
        text comment
        timestamptz created_at
    }

    schema_migrations {
        text version PK
        timestamptz applied_at
    }

    users ||--o{ user_skills : "имеет"
    skills ||--o{ user_skills : "используется в"
    users ||--o{ sessions : "ментор"
    users ||--o{ sessions : "ученик"
    skills ||--o{ sessions : "тема"
    users ||--o{ chat_messages : "отправляет"
    users ||--o{ chat_messages : "получает"
    users ||--o{ reviews : "пишет"
    users ||--o{ reviews : "получает"
    sessions ||--o{ reviews : "основа для"
```

---

## Sequence диаграмма: запись ученика на сессию

```mermaid
sequenceDiagram
    actor Ученик
    actor Ментор
    participant Фронтенд
    participant Flask
    participant PostgreSQL
    participant Redis

    Ученик->>Фронтенд: Открыть профиль ментора
    Фронтенд->>Flask: GET /api/mentors/:id
    Flask->>PostgreSQL: SELECT users + reviews + skills
    PostgreSQL-->>Flask: данные ментора
    Flask-->>Фронтенд: {mentor, skills, reviews}
    Фронтенд-->>Ученик: Показать профиль

    Ученик->>Фронтенд: Нажать «Записаться»
    Фронтенд->>Flask: POST /api/sessions (JWT)
    Flask->>Flask: Проверить JWT токен
    Flask->>PostgreSQL: INSERT INTO sessions (pending)
    PostgreSQL-->>Flask: {session_id}
    Flask-->>Фронтенд: 201 {session}
    Фронтенд-->>Ученик: «Запрос отправлен»

    Note over Ментор,Redis: Ментор видит входящий запрос

    Ментор->>Фронтенд: Открыть страницу сессий
    Фронтенд->>Flask: GET /api/sessions (JWT)
    Flask->>PostgreSQL: SELECT sessions WHERE mentor_id = ?
    PostgreSQL-->>Flask: список сессий
    Flask-->>Фронтенд: {upcoming, past, pending}
    Фронтенд-->>Ментор: Показать pending-запросы

    Ментор->>Фронтенд: Подтвердить сессию
    Фронтенд->>Flask: PUT /api/sessions/:id {status: confirmed}
    Flask->>PostgreSQL: UPDATE sessions SET status = confirmed
    PostgreSQL-->>Flask: обновлённая сессия
    Flask-->>Фронтенд: 200 {session}
    Фронтенд-->>Ментор: Статус обновлён
```

---

## Component/Deployment диаграмма

```mermaid
graph TB
    subgraph Клиент["Браузер пользователя"]
        Browser[React SPA<br/>TypeScript + Tailwind]
    end

    subgraph Docker["Docker Compose (сервер)"]
        subgraph nginx_block["nginx:1.27"]
            Nginx[Реверс-прокси<br/>:8080]
        end

        subgraph frontend_block["frontend контейнер"]
            Frontend[React SPA<br/>собранный Vite<br/>nginx:alpine]
        end

        subgraph app_block["app контейнер"]
            Gunicorn[gunicorn<br/>GracefulSyncWorker]
            Flask[Flask приложение<br/>blueprints: auth, users,<br/>skills, sessions, chat,<br/>reviews, health]
        end

        subgraph migrate_block["migrate контейнер (одноразовый)"]
            CLI[python cli.py migrate<br/>применяет SQL-миграции<br/>и завершается]
        end

        subgraph db_block["db контейнер"]
            Postgres[(PostgreSQL 16.2<br/>volume: pgdata)]
        end

        subgraph redis_block["redis контейнер"]
            Redis[(Redis 7.2.4<br/>кэш + счётчики)]
        end
    end

    subgraph CICD["GitHub Actions CI/CD"]
        GH[github.com<br/>ghcr.io образы]
    end

    Browser -->|HTTP :8080| Nginx
    Nginx -->|/* статика| Frontend
    Nginx -->|/api/* /health| Gunicorn
    Gunicorn --> Flask
    Flask -->|psycopg2| Postgres
    Flask -->|redis-py| Redis
    CLI -->|psycopg2| Postgres
    GH -->|docker pull| Docker
```
