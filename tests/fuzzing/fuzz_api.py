"""
Фаззинг-тесты публичных эндпоинтов платформы взаимного обучения.

Проверяются:
- SQL-инъекции
- XSS-пэйлоады
- Граничные значения (пустые строки, None, очень длинные строки)
- Некорректные типы данных
- Отрицательные числа / невалидные значения

Запуск:
    pytest tests/fuzzing/fuzz_api.py -v

Для запуска нужен рабочий сервер (localhost:5000) или укажи BASE_URL:
    BASE_URL=http://localhost:8080 pytest tests/fuzzing/fuzz_api.py -v
"""
import os
import uuid

import pytest
import requests

BASE_URL = os.getenv("BASE_URL", "http://localhost:5000")

# ---------------------------------------------------------------------------
# Наборы пэйлоадов
# ---------------------------------------------------------------------------

SQL_INJECTIONS = [
    "' OR 1=1 --",
    "'; DROP TABLE users; --",
    "1; SELECT * FROM users --",
    "' UNION SELECT null, null, null --",
    "\" OR \"\"=\"",
    "admin'--",
    "' OR 'x'='x",
]

XSS_PAYLOADS = [
    "<script>alert(1)</script>",
    "<img src=x onerror=alert(1)>",
    "javascript:alert(1)",
    "<svg onload=alert(1)>",
    "';alert(1)//",
    "<iframe src='javascript:alert(1)'></iframe>",
]

BOUNDARY_VALUES = [
    "",
    " ",
    "   ",
    None,
    "a" * 10_000,
    "a" * 65_536,
    "\x00",
    "\n\r\t",
    "null",
    "undefined",
    "NaN",
    "Infinity",
    "0",
    "true",
    "false",
    "[]",
    "{}",
]

BAD_TYPES = [
    42,
    -1,
    0,
    3.14,
    True,
    False,
    [],
    {},
    [1, 2, 3],
    {"key": "value"},
]


# ---------------------------------------------------------------------------
# Вспомогательные функции
# ---------------------------------------------------------------------------

def register_and_login() -> tuple[str, int]:
    """Регистрирует уникального пользователя и возвращает (token, user_id)."""
    email = f"fuzz_{uuid.uuid4().hex[:8]}@test.com"
    resp = requests.post(f"{BASE_URL}/api/auth/register", json={
        "email": email,
        "password": "Fuzz1234!",
        "name": "Фаззер",
    })
    assert resp.status_code == 201, f"Регистрация не удалась: {resp.text}"
    data = resp.json()
    return data["token"], data["user"]["id"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def assert_safe(resp: requests.Response, payload):
    """Убеждаемся, что сервер не упал (500) и не вернул стек в ответе."""
    assert resp.status_code != 500, (
        f"Сервер упал (500) на пэйлоаде {payload!r}.\nОтвет: {resp.text[:300]}"
    )
    body = resp.text.lower()
    for leak in ("traceback", "psycopg2", "syntax error", "pg_query"):
        assert leak not in body, (
            f"Утечка деталей БД на пэйлоаде {payload!r}.\nОтвет: {resp.text[:300]}"
        )


# ---------------------------------------------------------------------------
# Регистрация / авторизация
# ---------------------------------------------------------------------------

class TestAuthFuzzing:

    @pytest.mark.parametrize("payload", SQL_INJECTIONS + XSS_PAYLOADS + BOUNDARY_VALUES)
    def test_register_email_fuzzing(self, payload):
        """SQL-инъекции и XSS в поле email при регистрации."""
        resp = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": payload,
            "password": "Password123",
            "name": "Тест",
        })
        assert_safe(resp, payload)
        assert resp.status_code in (400, 409, 422), (
            f"Неожиданный статус {resp.status_code} на email={payload!r}"
        )

    @pytest.mark.parametrize("payload", SQL_INJECTIONS + XSS_PAYLOADS + BOUNDARY_VALUES)
    def test_register_name_fuzzing(self, payload):
        """SQL-инъекции и XSS в поле name при регистрации."""
        resp = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": f"test_{uuid.uuid4().hex[:6]}@test.com",
            "password": "Password123",
            "name": payload,
        })
        assert_safe(resp, payload)

    @pytest.mark.parametrize("payload", SQL_INJECTIONS + BOUNDARY_VALUES)
    def test_login_fuzzing(self, payload):
        """SQL-инъекции при логине (не должны давать доступ)."""
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": payload,
            "password": payload,
        })
        assert_safe(resp, payload)
        assert resp.status_code in (400, 401), (
            f"SQL-инъекция дала доступ: {resp.status_code}"
        )


# ---------------------------------------------------------------------------
# Навыки
# ---------------------------------------------------------------------------

class TestSkillsFuzzing:

    @pytest.mark.parametrize("payload", SQL_INJECTIONS + XSS_PAYLOADS)
    def test_skills_search_sql_injection(self, payload):
        """SQL-инъекции через параметр search в каталоге навыков."""
        resp = requests.get(f"{BASE_URL}/api/skills", params={"search": payload})
        assert_safe(resp, payload)
        assert resp.status_code == 200

    @pytest.mark.parametrize("payload", SQL_INJECTIONS + XSS_PAYLOADS + BOUNDARY_VALUES)
    def test_create_skill_fuzzing(self, payload):
        """Фаззинг создания навыка."""
        token, _ = register_and_login()
        resp = requests.post(
            f"{BASE_URL}/api/skills",
            json={"name": payload, "category": payload},
            headers=auth_headers(token),
        )
        assert_safe(resp, payload)

    @pytest.mark.parametrize("skill_id", [-1, 0, 999999, "abc", None, "' OR 1=1 --"])
    def test_skill_invalid_id(self, skill_id):
        """Невалидные ID навыков."""
        resp = requests.get(f"{BASE_URL}/api/skills/{skill_id}")
        assert_safe(resp, skill_id)
        assert resp.status_code in (400, 404)


# ---------------------------------------------------------------------------
# Сессии
# ---------------------------------------------------------------------------

class TestSessionsFuzzing:

    def test_create_session_missing_fields(self):
        """Создание сессии с пустым телом."""
        token, _ = register_and_login()
        resp = requests.post(
            f"{BASE_URL}/api/sessions",
            json={},
            headers=auth_headers(token),
        )
        assert_safe(resp, {})
        assert resp.status_code == 400

    @pytest.mark.parametrize("payload", BAD_TYPES)
    def test_create_session_bad_mentor_id(self, payload):
        """Неверный тип mentor_id."""
        token, _ = register_and_login()
        resp = requests.post(
            f"{BASE_URL}/api/sessions",
            json={"mentor_id": payload, "skill_id": 1, "scheduled_at": "2025-01-01T10:00:00", "topic": "тест"},
            headers=auth_headers(token),
        )
        assert_safe(resp, payload)

    @pytest.mark.parametrize("payload", SQL_INJECTIONS + XSS_PAYLOADS + BOUNDARY_VALUES)
    def test_create_session_topic_fuzzing(self, payload):
        """XSS и SQL в поле topic."""
        token, _ = register_and_login()
        resp = requests.post(
            f"{BASE_URL}/api/sessions",
            json={"mentor_id": 1, "skill_id": 1, "scheduled_at": "2025-01-01T10:00:00", "topic": payload},
            headers=auth_headers(token),
        )
        assert_safe(resp, payload)

    def test_session_self_booking(self):
        """Нельзя записаться к самому себе в качестве ментора."""
        token, user_id = register_and_login()
        resp = requests.post(
            f"{BASE_URL}/api/sessions",
            json={"mentor_id": user_id, "skill_id": 1, "scheduled_at": "2025-06-01T10:00:00", "topic": "тест"},
            headers=auth_headers(token),
        )
        assert_safe(resp, "self-booking")
        assert resp.status_code in (400, 422), (
            f"Самозапись не заблокирована: статус {resp.status_code}"
        )

    @pytest.mark.parametrize("status", ["'; DROP TABLE sessions; --", "<script>", "", "superadmin", 42, None])
    def test_update_session_invalid_status(self, status):
        """Невалидные значения статуса сессии."""
        token, _ = register_and_login()
        resp = requests.put(
            f"{BASE_URL}/api/sessions/1",
            json={"status": status},
            headers=auth_headers(token),
        )
        assert_safe(resp, status)
        assert resp.status_code in (400, 403, 404)


# ---------------------------------------------------------------------------
# Отзывы
# ---------------------------------------------------------------------------

class TestReviewsFuzzing:

    @pytest.mark.parametrize("rating", [-1, 0, 6, 100, -100, 3.5, "5", None, "' OR 1=1"])
    def test_create_review_invalid_rating(self, rating):
        """Невалидные значения рейтинга."""
        token, _ = register_and_login()
        resp = requests.post(
            f"{BASE_URL}/api/reviews",
            json={"reviewee_id": 1, "session_id": 1, "rating": rating},
            headers=auth_headers(token),
        )
        assert_safe(resp, rating)
        if not isinstance(rating, int) or not (1 <= rating <= 5):
            assert resp.status_code in (400, 403, 404, 422)

    @pytest.mark.parametrize("payload", SQL_INJECTIONS + XSS_PAYLOADS + BOUNDARY_VALUES)
    def test_review_comment_fuzzing(self, payload):
        """XSS и SQL в поле comment отзыва."""
        token, _ = register_and_login()
        resp = requests.post(
            f"{BASE_URL}/api/reviews",
            json={"reviewee_id": 1, "session_id": 1, "rating": 5, "comment": payload},
            headers=auth_headers(token),
        )
        assert_safe(resp, payload)


# ---------------------------------------------------------------------------
# Чат
# ---------------------------------------------------------------------------

class TestChatFuzzing:

    @pytest.mark.parametrize("payload", SQL_INJECTIONS + XSS_PAYLOADS + BOUNDARY_VALUES)
    def test_send_message_text_fuzzing(self, payload):
        """XSS и SQL в тексте чат-сообщения."""
        token, _ = register_and_login()
        resp = requests.post(
            f"{BASE_URL}/api/chat/1",
            json={"text": payload},
            headers=auth_headers(token),
        )
        assert_safe(resp, payload)

    @pytest.mark.parametrize("user_id", [-1, 0, 999999, "abc", "' OR 1=1"])
    def test_chat_invalid_user_id(self, user_id):
        """Невалидные user_id в URL чата."""
        token, _ = register_and_login()
        resp = requests.get(
            f"{BASE_URL}/api/chat/{user_id}",
            headers=auth_headers(token),
        )
        assert_safe(resp, user_id)
        assert resp.status_code in (200, 400, 404)


# ---------------------------------------------------------------------------
# Авторизация (заголовки)
# ---------------------------------------------------------------------------

class TestAuthHeaderFuzzing:

    @pytest.mark.parametrize("token", [
        "",
        "Bearer ",
        "Bearer invalid.token.here",
        "Bearer ' OR 1=1 --",
        f"Bearer {'a' * 1000}",
        "Basic dXNlcjpwYXNz",
        None,
        "bearer token",
    ])
    def test_invalid_auth_header(self, token):
        """Невалидные Authorization-заголовки."""
        headers = {"Authorization": token} if token is not None else {}
        resp = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        assert_safe(resp, token)
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Health-эндпоинт
# ---------------------------------------------------------------------------

class TestHealthFuzzing:

    def test_health_responds(self):
        """/health должен отвечать 200 или 503 (никогда не 500)."""
        resp = requests.get(f"{BASE_URL}/health")
        assert resp.status_code in (200, 503)
        data = resp.json()
        assert "status" in data
        assert "checks" in data
        assert "database" in data["checks"]
        assert "redis" in data["checks"]
