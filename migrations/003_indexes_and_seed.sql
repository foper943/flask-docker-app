-- Индексы на часто запрашиваемые поля

CREATE INDEX IF NOT EXISTS idx_user_skills_user_id  ON user_skills(user_id);
CREATE INDEX IF NOT EXISTS idx_user_skills_skill_id ON user_skills(skill_id);
CREATE INDEX IF NOT EXISTS idx_user_skills_type     ON user_skills(type);

CREATE INDEX IF NOT EXISTS idx_sessions_mentor_id   ON sessions(mentor_id);
CREATE INDEX IF NOT EXISTS idx_sessions_learner_id  ON sessions(learner_id);
CREATE INDEX IF NOT EXISTS idx_sessions_status      ON sessions(status);
CREATE INDEX IF NOT EXISTS idx_sessions_skill_id    ON sessions(skill_id);

CREATE INDEX IF NOT EXISTS idx_chat_messages_sender   ON chat_messages(sender_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_receiver ON chat_messages(receiver_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_pair     ON chat_messages(LEAST(sender_id, receiver_id), GREATEST(sender_id, receiver_id));

CREATE INDEX IF NOT EXISTS idx_reviews_reviewee_id ON reviews(reviewee_id);
CREATE INDEX IF NOT EXISTS idx_reviews_session_id  ON reviews(session_id);

-- Тестовые пользователи (пароль: Password123 для всех)
-- хэш bcrypt: werkzeug.security.generate_password_hash('Password123')
INSERT INTO users (email, password_hash, name, bio, role) VALUES
    ('anna@example.com',
     'pbkdf2:sha256:260000$xK9mLqR2$3a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b',
     'Анна Смирнова', 'Python-разработчик с 5-летним опытом. Люблю обучать!', 'mentor'),
    ('boris@example.com',
     'pbkdf2:sha256:260000$xK9mLqR2$3a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b',
     'Борис Иванов', 'Fullstack JS: React + Node.js. Готов делиться знаниями.', 'mentor'),
    ('vera@example.com',
     'pbkdf2:sha256:260000$xK9mLqR2$3a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b',
     'Вера Козлова', 'Data Scientist. Специализируюсь на ML и визуализации данных.', 'mentor'),
    ('dmitry@example.com',
     'pbkdf2:sha256:260000$xK9mLqR2$3a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b',
     'Дмитрий Новиков', 'DevOps-инженер. Docker, Kubernetes, CI/CD.', 'mentor'),
    ('elena@example.com',
     'pbkdf2:sha256:260000$xK9mLqR2$3a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b',
     'Елена Фёдорова', 'Преподаватель английского. IELTS 8.0.', 'mentor'),
    ('ivan@example.com',
     'pbkdf2:sha256:260000$xK9mLqR2$3a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b',
     'Иван Петров', 'Студент. Учу Python и ML.', 'learner'),
    ('maria@example.com',
     'pbkdf2:sha256:260000$xK9mLqR2$3a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b',
     'Мария Сидорова', 'Начинающий веб-разработчик. Изучаю React.', 'learner'),
    ('nikita@example.com',
     'pbkdf2:sha256:260000$xK9mLqR2$3a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b',
     'Никита Орлов', 'Хочу освоить Docker и деплой приложений.', 'learner'),
    ('olga@example.com',
     'pbkdf2:sha256:260000$xK9mLqR2$3a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b',
     'Ольга Волкова', 'Аналитик данных. Изучаю SQL и Python.', 'learner'),
    ('pavel@example.com',
     'pbkdf2:sha256:260000$xK9mLqR2$3a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b',
     'Павел Зайцев', 'Хочу улучшить английский для работы в IT.', 'learner')
ON CONFLICT (email) DO NOTHING;

-- Связи менторов с навыками (teaching)
INSERT INTO user_skills (user_id, skill_id, type)
SELECT u.id, s.id, 'teaching'
FROM users u, skills s
WHERE (u.email = 'anna@example.com'  AND s.name IN ('Python', 'SQL'))
   OR (u.email = 'boris@example.com' AND s.name IN ('JavaScript', 'React'))
   OR (u.email = 'vera@example.com'  AND s.name IN ('Machine Learning', 'Python', 'SQL'))
   OR (u.email = 'dmitry@example.com' AND s.name IN ('Docker', 'Git'))
   OR (u.email = 'elena@example.com' AND s.name IN ('English'))
ON CONFLICT DO NOTHING;

-- Связи учеников с навыками (learning)
INSERT INTO user_skills (user_id, skill_id, type)
SELECT u.id, s.id, 'learning'
FROM users u, skills s
WHERE (u.email = 'ivan@example.com'   AND s.name IN ('Python', 'Machine Learning'))
   OR (u.email = 'maria@example.com'  AND s.name IN ('React', 'JavaScript'))
   OR (u.email = 'nikita@example.com' AND s.name IN ('Docker', 'Git'))
   OR (u.email = 'olga@example.com'   AND s.name IN ('SQL', 'Python'))
   OR (u.email = 'pavel@example.com'  AND s.name IN ('English'))
ON CONFLICT DO NOTHING;

-- Тестовые сессии (разные статусы)
INSERT INTO sessions (mentor_id, learner_id, skill_id, status, scheduled_at, topic)
SELECT
    mentor.id, learner.id, skill.id,
    sess.status,
    sess.scheduled_at::timestamptz,
    sess.topic
FROM (VALUES
    ('anna@example.com',   'ivan@example.com',   'Python',          'completed', '2024-11-01 10:00+03', 'Введение в Python: списки и словари'),
    ('anna@example.com',   'olga@example.com',   'Python',          'completed', '2024-11-15 14:00+03', 'ООП в Python: классы и наследование'),
    ('anna@example.com',   'ivan@example.com',   'SQL',             'confirmed', '2024-12-20 11:00+03', 'SQL: оконные функции'),
    ('boris@example.com',  'maria@example.com',  'React',           'completed', '2024-11-10 16:00+03', 'React Hooks: useState и useEffect'),
    ('boris@example.com',  'maria@example.com',  'JavaScript',      'completed', '2024-11-25 15:00+03', 'Асинхронный JavaScript: Promise и async/await'),
    ('boris@example.com',  'nikita@example.com', 'JavaScript',      'pending',   '2024-12-28 13:00+03', 'TypeScript: основы типизации'),
    ('vera@example.com',   'ivan@example.com',   'Machine Learning','completed', '2024-11-20 10:00+03', 'Линейная регрессия на практике'),
    ('vera@example.com',   'olga@example.com',   'Machine Learning','confirmed', '2024-12-22 12:00+03', 'Кластеризация: k-means'),
    ('dmitry@example.com', 'nikita@example.com', 'Docker',          'completed', '2024-11-05 09:00+03', 'Docker: создание и запуск контейнеров'),
    ('dmitry@example.com', 'nikita@example.com', 'Git',             'completed', '2024-11-18 10:00+03', 'Git: ветвление и merge-стратегии'),
    ('dmitry@example.com', 'maria@example.com',  'Docker',          'pending',   '2024-12-30 14:00+03', 'Docker Compose: многоконтейнерные приложения'),
    ('elena@example.com',  'pavel@example.com',  'English',         'completed', '2024-11-12 18:00+03', 'Business English: переговоры и презентации'),
    ('elena@example.com',  'pavel@example.com',  'English',         'completed', '2024-11-26 18:00+03', 'IELTS Speaking: практика'),
    ('elena@example.com',  'ivan@example.com',   'English',         'confirmed', '2024-12-21 19:00+03', 'Technical English для разработчиков'),
    ('anna@example.com',   'maria@example.com',  'Python',          'pending',   '2024-12-29 11:00+03', 'Python для фронтендера: скрипты и автоматизация')
) AS sess(mentor_email, learner_email, skill_name, status, scheduled_at, topic)
JOIN users mentor  ON mentor.email  = sess.mentor_email
JOIN users learner ON learner.email = sess.learner_email
JOIN skills skill  ON skill.name    = sess.skill_name
ON CONFLICT DO NOTHING;

-- Отзывы на завершённые сессии
INSERT INTO reviews (reviewer_id, reviewee_id, session_id, rating, comment)
SELECT
    learner.id,
    mentor.id,
    s.id,
    rev.rating,
    rev.comment
FROM (VALUES
    ('anna@example.com',  'ivan@example.com',  'Python',          'completed', '2024-11-01 10:00+03', 5, 'Отличное занятие! Анна объясняет очень понятно.'),
    ('anna@example.com',  'olga@example.com',  'Python',          'completed', '2024-11-15 14:00+03', 5, 'Очень структурированная подача материала.'),
    ('boris@example.com', 'maria@example.com', 'React',           'completed', '2024-11-10 16:00+03', 4, 'Хороший урок, разобрались с хуками.'),
    ('boris@example.com', 'maria@example.com', 'JavaScript',      'completed', '2024-11-25 15:00+03', 5, 'Борис — отличный ментор, всё разложил по полочкам.'),
    ('vera@example.com',  'ivan@example.com',  'Machine Learning','completed', '2024-11-20 10:00+03', 5, 'Вера — эксперт в ML, занятие было очень полезным!'),
    ('dmitry@example.com','nikita@example.com','Docker',          'completed', '2024-11-05 09:00+03', 4, 'Дмитрий хорошо знает Docker, всё чётко объяснил.'),
    ('dmitry@example.com','nikita@example.com','Git',             'completed', '2024-11-18 10:00+03', 5, 'Наконец-то разобрался с rebase и cherry-pick!'),
    ('elena@example.com', 'pavel@example.com', 'English',         'completed', '2024-11-12 18:00+03', 5, 'Елена — профессиональный преподаватель. Очень рекомендую!'),
    ('elena@example.com', 'pavel@example.com', 'English',         'completed', '2024-11-26 18:00+03', 5, 'Второе занятие ещё лучше первого. Прогресс заметен.')
) AS rev(mentor_email, learner_email, skill_name, status, scheduled_at, rating, comment)
JOIN users mentor  ON mentor.email  = rev.mentor_email
JOIN users learner ON learner.email = rev.learner_email
JOIN sessions s ON s.mentor_id = mentor.id
              AND s.learner_id = learner.id
              AND s.status = rev.status
              AND s.scheduled_at = rev.scheduled_at::timestamptz
ON CONFLICT DO NOTHING;
