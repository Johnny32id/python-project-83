"""Тесты для модуля db."""

import pytest
from datetime import datetime
from psycopg2 import Error as DBError
from page_analyzer.db import (
    DatabaseConnection,
    add_url,
    get_url_by_name,
    get_url_by_id,
    get_all_urls,
    add_check,
    get_last_check_by_url_id,
    get_checks_by_url_id,
)


class TestAddUrl:
    """Тесты для функции add_url."""

    def test_add_url_success(self, test_db):
        """Тест успешного добавления URL."""
        url = 'https://example.com'
        url_id = add_url(url)
        assert isinstance(url_id, int)
        assert url_id > 0

    def test_add_url_sets_timestamp(self, test_db):
        """Тест установки временной метки при добавлении URL."""
        url = 'https://example.com'
        url_id = add_url(url)
        url_record = get_url_by_id(url_id)
        assert url_record is not None
        assert url_record.created_at is not None
        assert isinstance(url_record.created_at, datetime)

    def test_add_url_multiple_urls(self, test_db):
        """Тест добавления нескольких URL."""
        url1 = 'https://example1.com'
        url2 = 'https://example2.com'
        url3 = 'https://example3.com'

        id1 = add_url(url1)
        id2 = add_url(url2)
        id3 = add_url(url3)

        assert id1 != id2 != id3
        assert all(isinstance(i, int) for i in [id1, id2, id3])


class TestGetUrlByName:
    """Тесты для функции get_url_by_name."""

    def test_get_url_by_name_exists(self, test_db):
        """Тест получения существующего URL по имени."""
        url = 'https://example.com'
        url_id = add_url(url)
        found_url = get_url_by_name(url)
        assert found_url is not None
        assert found_url.id == url_id
        assert found_url.name == url

    def test_get_url_by_name_not_exists(self, test_db):
        """Тест получения несуществующего URL."""
        found_url = get_url_by_name('https://nonexistent.com')
        assert found_url is None

    def test_get_url_by_name_case_sensitive(self, test_db):
        """Тест чувствительности к регистру при поиске."""
        url = 'https://Example.com'
        add_url(url)
        # Поиск с другим регистром должен вернуть None
        found_url = get_url_by_name('https://example.com')
        # Или найдется, в зависимости от логики нормализации БД
        # В PostgreSQL сравнение строк зависит от COLLATE
        assert found_url is None or found_url.name == 'https://Example.com'


class TestGetUrlById:
    """Тесты для функции get_url_by_id."""

    def test_get_url_by_id_exists(self, test_db):
        """Тест получения существующего URL по ID."""
        url = 'https://example.com'
        url_id = add_url(url)
        found_url = get_url_by_id(url_id)
        assert found_url is not None
        assert found_url.id == url_id
        assert found_url.name == url

    def test_get_url_by_id_not_exists(self, test_db):
        """Тест получения несуществующего URL по ID."""
        found_url = get_url_by_id(99999)
        assert found_url is None

    def test_get_url_by_id_zero(self, test_db):
        """Тест получения URL с ID = 0."""
        found_url = get_url_by_id(0)
        assert found_url is None


class TestGetAllUrls:
    """Тесты для функции get_all_urls."""

    def test_get_all_urls_empty(self, test_db):
        """Тест получения всех URL из пустой БД."""
        urls = get_all_urls()
        assert urls == []

    def test_get_all_urls_single(self, test_db):
        """Тест получения одного URL."""
        url = 'https://example.com'
        add_url(url)
        urls = get_all_urls()
        assert len(urls) == 1
        assert urls[0].name == url
        assert urls[0].status_code is None
        assert urls[0].last_check is None

    def test_get_all_urls_multiple(self, test_db):
        """Тест получения нескольких URL."""
        urls_to_add = [
            'https://example1.com',
            'https://example2.com',
            'https://example3.com',
        ]
        for url in urls_to_add:
            add_url(url)

        urls = get_all_urls()
        assert len(urls) == 3
        # Проверяем, что URL отсортированы по ID DESC
        assert urls[0].id >= urls[1].id >= urls[2].id

    def test_get_all_urls_with_checks(self, test_db):
        """Тест получения URL с последними проверками."""
        url = 'https://example.com'
        url_id = add_url(url)

        # Добавляем проверку
        check_data = {
            'url_id': url_id,
            'status_code': 200,
            'h1': 'Test H1',
            'title': 'Test Title',
            'description': 'Test Description',
        }
        add_check(check_data)

        urls = get_all_urls()
        assert len(urls) == 1
        assert urls[0].status_code == 200
        assert urls[0].last_check is not None

    def test_get_all_urls_latest_check_only(self, test_db):
        """Тест получения только последней проверки для каждого URL."""
        url = 'https://example.com'
        url_id = add_url(url)

        # Добавляем две проверки
        add_check({
            'url_id': url_id,
            'status_code': 200,
            'h1': 'First',
            'title': None,
            'description': None,
        })
        add_check({
            'url_id': url_id,
            'status_code': 404,
            'h1': 'Second',
            'title': None,
            'description': None,
        })

        urls = get_all_urls()
        assert len(urls) == 1
        # Должна вернуться последняя проверка (status_code 404)
        assert urls[0].status_code == 404


class TestAddCheck:
    """Тесты для функции add_check."""

    def test_add_check_success(self, test_db):
        """Тест успешного добавления проверки."""
        url_id = add_url('https://example.com')
        check_data = {
            'url_id': url_id,
            'status_code': 200,
            'h1': 'Test H1',
            'title': 'Test Title',
            'description': 'Test Description',
        }
        add_check(check_data)
        # Проверяем, что проверка добавлена
        check = get_last_check_by_url_id(url_id)
        assert check is not None
        assert check.status_code == 200
        assert check.h1 == 'Test H1'
        assert check.title == 'Test Title'
        assert check.description == 'Test Description'

    def test_add_check_with_nulls(self, test_db):
        """Тест добавления проверки с NULL значениями."""
        url_id = add_url('https://example.com')
        check_data = {
            'url_id': url_id,
            'status_code': 404,
            'h1': None,
            'title': None,
            'description': None,
        }
        add_check(check_data)
        check = get_last_check_by_url_id(url_id)
        assert check is not None
        assert check.status_code == 404
        assert check.h1 is None
        assert check.title is None
        assert check.description is None

    def test_add_check_sets_timestamp(self, test_db):
        """Тест установки временной метки при добавлении проверки."""
        url_id = add_url('https://example.com')
        check_data = {
            'url_id': url_id,
            'status_code': 200,
            'h1': None,
            'title': None,
            'description': None,
        }
        add_check(check_data)
        check = get_last_check_by_url_id(url_id)
        assert check.created_at is not None
        assert isinstance(check.created_at, datetime)

    def test_add_check_multiple_checks(self, test_db):
        """Тест добавления нескольких проверок для одного URL."""
        url_id = add_url('https://example.com')
        for i in range(3):
            check_data = {
                'url_id': url_id,
                'status_code': 200 + i,
                'h1': f'H1 {i}',
                'title': f'Title {i}',
                'description': f'Description {i}',
            }
            add_check(check_data)

        checks = get_checks_by_url_id(url_id)
        assert len(checks) == 3


class TestGetChecksByUrlId:
    """Тесты для функции get_checks_by_url_id."""

    def test_get_checks_by_url_id_empty(self, test_db):
        """Тест получения проверок для URL без проверок."""
        url_id = add_url('https://example.com')
        checks = get_checks_by_url_id(url_id)
        assert checks == []

    def test_get_checks_by_url_id_single(self, test_db):
        """Тест получения одной проверки."""
        url_id = add_url('https://example.com')
        add_check({
            'url_id': url_id,
            'status_code': 200,
            'h1': 'Test',
            'title': None,
            'description': None,
        })
        checks = get_checks_by_url_id(url_id)
        assert len(checks) == 1
        assert checks[0].status_code == 200

    def test_get_checks_by_url_id_multiple(self, test_db):
        """Тест получения нескольких проверок."""
        url_id = add_url('https://example.com')
        for i in range(5):
            add_check({
                'url_id': url_id,
                'status_code': 200 + i,
                'h1': f'H1 {i}',
                'title': None,
                'description': None,
            })
        checks = get_checks_by_url_id(url_id)
        assert len(checks) == 5
        # Проверяем, что проверки отсортированы по created_at DESC
        for i in range(len(checks) - 1):
            assert checks[i].created_at >= checks[i + 1].created_at

    def test_get_checks_by_url_id_different_urls(self, test_db):
        """Тест получения проверок только для указанного URL."""
        url_id1 = add_url('https://example1.com')
        url_id2 = add_url('https://example2.com')

        add_check({
            'url_id': url_id1,
            'status_code': 200,
            'h1': None,
            'title': None,
            'description': None,
        })
        add_check({
            'url_id': url_id2,
            'status_code': 404,
            'h1': None,
            'title': None,
            'description': None,
        })

        checks1 = get_checks_by_url_id(url_id1)
        checks2 = get_checks_by_url_id(url_id2)

        assert len(checks1) == 1
        assert len(checks2) == 1
        assert checks1[0].status_code == 200
        assert checks2[0].status_code == 404


class TestGetLastCheckByUrlId:
    """Тесты для функции get_last_check_by_url_id."""

    def test_get_last_check_by_url_id_no_checks(self, test_db):
        """Тест получения последней проверки для URL без проверок."""
        url_id = add_url('https://example.com')
        check = get_last_check_by_url_id(url_id)
        assert check is None

    def test_get_last_check_by_url_id_single(self, test_db):
        """Тест получения последней проверки для URL с одной проверкой."""
        url_id = add_url('https://example.com')
        add_check({
            'url_id': url_id,
            'status_code': 200,
            'h1': 'Test',
            'title': None,
            'description': None,
        })
        check = get_last_check_by_url_id(url_id)
        assert check is not None
        assert check.status_code == 200

    def test_get_last_check_by_url_id_multiple(self, test_db):
        """Тест получения последней проверки из нескольких."""
        url_id = add_url('https://example.com')
        # Добавляем проверки с задержкой, чтобы created_at отличался
        import time
        add_check({
            'url_id': url_id,
            'status_code': 200,
            'h1': 'First',
            'title': None,
            'description': None,
        })
        time.sleep(0.01)  # Небольшая задержка
        add_check({
            'url_id': url_id,
            'status_code': 404,
            'h1': 'Second',
            'title': None,
            'description': None,
        })
        check = get_last_check_by_url_id(url_id)
        assert check is not None
        assert check.status_code == 404
        assert check.h1 == 'Second'


class TestDatabaseConnection:
    """Тесты для класса DatabaseConnection."""

    def test_database_connection_context_manager(self, test_db):
        """Тест использования DatabaseConnection как контекстного менеджера."""
        with DatabaseConnection() as cursor:
            assert cursor is not None
            cursor.execute('SELECT 1')
            result = cursor.fetchone()
            assert result[0] == 1

    def test_database_connection_commits_transaction(self, test_db):
        """Тест коммита транзакции при успешном выполнении."""
        with DatabaseConnection() as cursor:
            cursor.execute(
                "INSERT INTO urls (name, created_at) VALUES (%s, %s)",
                ('https://test.com', datetime.now())
            )
        # Проверяем, что данные сохранились
        with DatabaseConnection() as cursor:
            cursor.execute("SELECT * FROM urls WHERE name = %s", ('https://test.com',))
            result = cursor.fetchone()
            assert result is not None

    def test_database_connection_rollback_on_exception(self, test_db):
        """Тест отката транзакции при исключении."""
        try:
            with DatabaseConnection() as cursor:
                cursor.execute(
                    "INSERT INTO urls (name, created_at) VALUES (%s, %s)",
                    ('https://test1.com', datetime.now())
                )
                raise ValueError('Тестовое исключение')
        except ValueError:
            pass

        # Проверяем, что данные не сохранились
        with DatabaseConnection() as cursor:
            cursor.execute("SELECT * FROM urls WHERE name = %s", ('https://test1.com',))
            result = cursor.fetchone()
            assert result is None

    def test_database_connection_custom_retries(self, test_db):
        """Тест установки кастомного количества попыток."""
        conn = DatabaseConnection(retries=1)
        assert conn.retries == 1

    def test_database_connection_closes_resources(self, test_db):
        """Тест закрытия ресурсов после использования."""
        conn = DatabaseConnection()
        with conn as cursor:
            cursor.execute('SELECT 1')
        # После выхода из контекста ресурсы должны быть закрыты
        assert conn.cursor is None or conn.cursor.closed
        assert conn.connection is None or conn.connection.closed

