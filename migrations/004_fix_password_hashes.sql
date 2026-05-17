-- Исправление хэшей паролей тестовых пользователей (пароль: Password123)
UPDATE users SET password_hash = 'pbkdf2:sha256:1000000$yQu8lNRT5celvpfl$ac2339c97edead91647284335969bb73459d38655dbd0a5a7b26e3997949b254'
WHERE email IN (
    'anna@example.com',
    'boris@example.com',
    'vera@example.com',
    'dmitry@example.com',
    'elena@example.com',
    'ivan@example.com',
    'maria@example.com',
    'nikita@example.com',
    'olga@example.com',
    'pavel@example.com'
);
