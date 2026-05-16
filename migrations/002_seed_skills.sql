-- Начальные данные: базовые навыки платформы (идемпотентно через ON CONFLICT DO NOTHING)

INSERT INTO skills (name, category, description) VALUES
    ('Python',           'Программирование', 'Язык программирования Python'),
    ('JavaScript',       'Программирование', 'JavaScript и экосистема Node.js'),
    ('React',            'Программирование', 'Библиотека для построения UI'),
    ('Machine Learning', 'Data Science',     'Основы ML и нейронных сетей'),
    ('SQL',              'Базы данных',      'Реляционные базы данных и SQL'),
    ('Docker',           'DevOps',           'Контейнеризация приложений'),
    ('Git',              'Инструменты',      'Система контроля версий'),
    ('English',          'Языки',            'Английский язык')
ON CONFLICT (name) DO NOTHING;
