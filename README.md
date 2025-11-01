### Hexlet tests and linter status:
[![Actions Status](https://github.com/Johnny32id/python-project-83/actions/workflows/hexlet-check.yml/badge.svg)](https://github.com/Johnny32id/python-project-83/actions)
[![Lint](https://github.com/Johnny32id/python-project-83/actions/workflows/lint.yml/badge.svg)](https://github.com/Johnny32id/python-project-83/actions/workflows/lint.yml)
[![Maintainability](https://api.codeclimate.com/v1/badges/7333744bb40db0efe850/maintainability)](https://codeclimate.com/github/Johnny32id/python-project-83/maintainability)

***Анализатор страниц предназначен для проверки сайтов на SEO-пригодность***

## Описание

Анализатор страниц - это веб-приложение на Flask, которое позволяет:
- Добавлять URL для анализа
- Проверять страницы на SEO-пригодность
- Анализировать HTML-контент (h1, title, description)
- Отслеживать статус HTTP-ответов
- Просматривать историю проверок для каждого URL

## Установка

### Требования

- Python 3.10+
- PostgreSQL
- Poetry (для управления зависимостями)

### Шаги установки

1. Установите Poetry (если не установлен):
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

2. Установите зависимости:
```bash
make install
```

3. Настройте базу данных:
   - Создайте базу данных PostgreSQL
   - Выполните скрипт `database.sql` для создания схемы
   - Настройте переменные окружения в `.env` файле

4. Создайте `.env` файл:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/page_analyzer_db
SECRET_KEY=your-secret-key-here  # Опционально, будет сгенерирован автоматически
```

## Запуск

### Режим разработки

```bash
make dev
```

### Production режим

```bash
make start
```

Приложение будет доступно по адресу `http://localhost:8000` (или указанному порту).

## Тестирование

Запуск всех тестов:
```bash
make test
```

Запуск тестов с покрытием:
```bash
make test-cov
```

## Технологии

- **Flask** - веб-фреймворк
- **PostgreSQL** - база данных
- **BeautifulSoup4** - парсинг HTML
- **Requests** - HTTP-клиент
- **Pytest** - тестирование

## Лицензия

Проект создан в рамках обучения на [Hexlet](https://hexlet.io)

***Демонстрационный проект можно посмотреть по [ссылке](https://python-project-83-gbc5.onrender.com/)***
