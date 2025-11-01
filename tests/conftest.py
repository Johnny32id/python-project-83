"""Конфигурация pytest для проекта."""

import os
import pytest
from psycopg2 import connect
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from psycopg2.extras import NamedTupleCursor
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()


@pytest.fixture(scope='function')
def test_db(monkeypatch):
    """Фикстура для настройки тестовой БД для каждого теста.

    Использует основную БД, но очищает данные перед каждым тестом.
    Переопределяет DATABASE_URL через monkeypatch.
    """
    # Получаем URL БД из переменных окружения
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        pytest.skip('DATABASE_URL не задан. Пропуск тестов БД.')

    # Переопределяем DATABASE_URL через monkeypatch
    monkeypatch.setenv('DATABASE_URL', db_url)
    # Перезагружаем конфигурацию, чтобы подхватить новое значение
    from importlib import reload
    from page_analyzer import config as config_module
    reload(config_module)
    config_module.config.DATABASE_URL = db_url

    # Подключаемся для очистки таблиц
    conn = connect(db_url)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    try:
        # Очищаем таблицы перед тестом
        cursor.execute('TRUNCATE TABLE url_checks CASCADE')
        cursor.execute('TRUNCATE TABLE urls CASCADE')
    finally:
        cursor.close()
        conn.close()

    yield db_url

    # Очищаем таблицы после теста
    conn = connect(db_url)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    try:
        cursor.execute('TRUNCATE TABLE url_checks CASCADE')
        cursor.execute('TRUNCATE TABLE urls CASCADE')
    finally:
        cursor.close()
        conn.close()
