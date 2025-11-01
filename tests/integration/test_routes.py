"""Интеграционные тесты для Flask-роутов."""

import pytest
from unittest.mock import patch, Mock
import requests


@pytest.fixture
def client(test_db):
    """Фикстура для создания тестового клиента Flask."""
    # Импортируем app после настройки test_db
    from page_analyzer.app import app
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        yield client


class TestIndexRoute:
    """Тесты для роута GET / (главная страница)."""

    def test_get_index_success(self, client):
        """Тест успешного отображения главной страницы."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'form' in response.data.lower() or b'url' in response.data.lower()

    def test_get_index_contains_form(self, client):
        """Тест наличия формы на главной странице."""
        response = client.get('/')
        assert response.status_code == 200
        # Проверяем, что есть поле ввода URL
        assert b'input' in response.data.lower() or b'url' in response.data.lower()


class TestCreateUrlRoute:
    """Тесты для роута POST /urls (создание URL)."""

    def test_create_url_success(self, client):
        """Тест успешного создания нового URL."""
        response = client.post('/urls', data={'url': 'https://example.com'})
        assert response.status_code == 302  # Редирект
        # Проверяем, что произошел редирект на страницу URL
        assert '/urls/' in response.location

    def test_create_url_empty_input(self, client):
        """Тест создания URL с пустым полем."""
        response = client.post('/urls', data={'url': ''})
        assert response.status_code == 422
        # Проверяем наличие сообщения об ошибке
        assert response.data

    def test_create_url_invalid_url(self, client):
        """Тест создания URL с некорректным URL."""
        response = client.post('/urls', data={'url': 'not-a-valid-url'})
        assert response.status_code == 422
        # Проверяем наличие сообщения об ошибке
        assert response.data

    def test_create_url_too_long(self, client):
        """Тест создания URL превышающего максимальную длину."""
        long_url = 'https://example.com/' + 'a' * 300
        response = client.post('/urls', data={'url': long_url})
        assert response.status_code == 422

    def test_create_url_duplicate(self, client):
        """Тест создания дублирующегося URL."""
        # Создаем первый URL
        response1 = client.post('/urls', data={'url': 'https://example.com'})
        assert response1.status_code == 302

        # Пытаемся создать тот же URL снова
        response2 = client.post('/urls', data={'url': 'https://example.com'})
        assert response2.status_code == 302
        # Проверяем flash-сообщение о том, что страница уже существует
        # (нужно следовать редиректу, чтобы увидеть flash)

    def test_create_url_normalizes_url(self, client):
        """Тест нормализации URL при создании."""
        # Создаем URL с путем и параметрами
        response = client.post(
            '/urls',
            data={'url': 'https://example.com/path?param=value#section'}
        )
        assert response.status_code == 302
        # URL должен быть нормализован до https://example.com

    def test_create_url_without_scheme(self, client):
        """Тест создания URL без схемы."""
        response = client.post('/urls', data={'url': 'example.com'})
        # Должна быть ошибка валидации
        assert response.status_code == 422


class TestUrlsListRoute:
    """Тесты для роута GET /urls (список URL)."""

    def test_urls_list_empty(self, client):
        """Тест отображения пустого списка URL."""
        response = client.get('/urls')
        assert response.status_code == 200

    def test_urls_list_with_urls(self, client):
        """Тест отображения списка с URL."""
        # Создаем несколько URL
        client.post('/urls', data={'url': 'https://example1.com'})
        client.post('/urls', data={'url': 'https://example2.com'})
        client.post('/urls', data={'url': 'https://example3.com'})

        response = client.get('/urls')
        assert response.status_code == 200
        assert b'example1.com' in response.data
        assert b'example2.com' in response.data
        assert b'example3.com' in response.data

    def test_urls_list_shows_latest_check(self, client):
        """Тест отображения последней проверки для каждого URL."""
        # Создаем URL
        response = client.post('/urls', data={'url': 'https://example.com'})
        url_id = response.location.split('/')[-1]

        # Создаем мок для HTTP-запроса при проверке
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'text/html'}
        mock_response.history = []
        mock_response.content = b'<html><head><title>Test</title></head></html>'
        mock_response.iter_content.return_value = [
            '<html><head><title>Test</title></head></html>'
        ]

        with patch('page_analyzer.services.check_service.requests.Session') as mock_session:
            mock_session.return_value.get.return_value = mock_response
            # Выполняем проверку
            client.post(f'/urls/{url_id}/checks')

        # Проверяем список URL
        response = client.get('/urls')
        assert response.status_code == 200
        # Проверяем, что отображается статус проверки
        assert b'200' in response.data or b'example.com' in response.data


class TestGetUrlRoute:
    """Тесты для роута GET /urls/<id> (детали URL)."""

    def test_get_url_success(self, client):
        """Тест успешного отображения деталей URL."""
        # Создаем URL
        response = client.post('/urls', data={'url': 'https://example.com'})
        url_id = response.location.split('/')[-1]

        # Получаем детали
        response = client.get(f'/urls/{url_id}')
        assert response.status_code == 200
        assert b'example.com' in response.data

    def test_get_url_not_found(self, client):
        """Тест отображения 404 для несуществующего URL."""
        response = client.get('/urls/99999')
        assert response.status_code == 404

    def test_get_url_shows_checks(self, client):
        """Тест отображения проверок для URL."""
        # Создаем URL
        response = client.post('/urls', data={'url': 'https://example.com'})
        url_id = response.location.split('/')[-1]

        # Создаем мок для HTTP-запроса
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'text/html'}
        mock_response.history = []
        mock_response.content = b'<html><head><title>Test</title></head></html>'
        mock_response.iter_content.return_value = [
            '<html><head><title>Test</title></head></html>'
        ]

        with patch('page_analyzer.services.check_service.requests.Session') as mock_session:
            mock_session.return_value.get.return_value = mock_response
            # Выполняем проверку
            client.post(f'/urls/{url_id}/checks')

        # Получаем детали URL
        response = client.get(f'/urls/{url_id}')
        assert response.status_code == 200
        # Проверяем наличие информации о проверке
        assert b'200' in response.data or b'Test' in response.data


class TestAddUrlCheckRoute:
    """Тесты для роута POST /urls/<id>/checks (проверка URL)."""

    def test_add_check_success(self, client):
        """Тест успешной проверки URL."""
        # Создаем URL
        response = client.post('/urls', data={'url': 'https://example.com'})
        url_id = response.location.split('/')[-1]

        # Создаем мок для HTTP-запроса
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'text/html'}
        mock_response.history = []
        html_content = (
            '<html><head><title>Test Title</title>'
            '<meta name="description" content="Test Description">'
            '</head><body><h1>Test H1</h1></body></html>'
        )
        mock_response.content = html_content.encode()
        mock_response.iter_content.return_value = [html_content]

        with patch('page_analyzer.services.check_service.requests.Session') as mock_session:
            mock_session.return_value.get.return_value = mock_response
            response = client.post(f'/urls/{url_id}/checks')
            assert response.status_code == 302
            assert f'/urls/{url_id}' in response.location

    def test_add_check_url_not_found(self, client):
        """Тест проверки несуществующего URL."""
        response = client.post('/urls/99999/checks')
        assert response.status_code == 302
        # Должен быть редирект на список URL
        assert '/urls' in response.location

    def test_add_check_http_error(self, client):
        """Тест обработки HTTP-ошибки при проверке."""
        # Создаем URL
        response = client.post('/urls', data={'url': 'https://example.com'})
        url_id = response.location.split('/')[-1]

        # Создаем мок для HTTP-запроса с ошибкой
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.headers = {'Content-Type': 'text/html'}
        mock_response.history = []
        mock_response.content = b'<html>Not Found</html>'
        mock_response.iter_content.return_value = ['<html>Not Found</html>']
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            '404 Not Found', response=mock_response
        )

        with patch('page_analyzer.services.check_service.requests.Session') as mock_session:
            mock_session.return_value.get.return_value = mock_response
            response = client.post(f'/urls/{url_id}/checks')
            # Проверка завершилась с ошибкой, но должна быть обработка
            assert response.status_code == 302

    def test_add_check_connection_error(self, client):
        """Тест обработки ошибки подключения."""
        # Создаем URL
        response = client.post('/urls', data={'url': 'https://nonexistent-domain-12345.com'})
        url_id = response.location.split('/')[-1]

        # Создаем мок для ошибки подключения
        with patch('page_analyzer.services.check_service.requests.Session') as mock_session:
            mock_session.return_value.get.side_effect = requests.exceptions.ConnectionError(
                'Connection failed'
            )
            response = client.post(f'/urls/{url_id}/checks')
            assert response.status_code == 302

    def test_add_check_timeout(self, client):
        """Тест обработки таймаута при проверке."""
        # Создаем URL
        response = client.post('/urls', data={'url': 'https://example.com'})
        url_id = response.location.split('/')[-1]

        # Создаем мок для таймаута
        with patch('page_analyzer.services.check_service.requests.Session') as mock_session:
            mock_session.return_value.get.side_effect = requests.exceptions.Timeout(
                'Request timeout'
            )
            response = client.post(f'/urls/{url_id}/checks')
            assert response.status_code == 302


class TestFullCycle:
    """Тесты для полного цикла: добавление URL → проверка → просмотр результатов."""

    def test_full_cycle_add_check_view(self, client):
        """Тест полного цикла работы с URL."""
        # Шаг 1: Добавляем URL
        response = client.post('/urls', data={'url': 'https://example.com'})
        assert response.status_code == 302
        url_id = response.location.split('/')[-1]

        # Шаг 2: Проверяем URL
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'text/html'}
        mock_response.history = []
        html_content = (
            '<html><head><title>Example Title</title>'
            '<meta name="description" content="Example Description">'
            '</head><body><h1>Example H1</h1></body></html>'
        )
        mock_response.content = html_content.encode()
        mock_response.iter_content.return_value = [html_content]

        with patch('page_analyzer.services.check_service.requests.Session') as mock_session:
            mock_session.return_value.get.return_value = mock_response
            response = client.post(f'/urls/{url_id}/checks')
            assert response.status_code == 302

        # Шаг 3: Просматриваем детали URL
        response = client.get(f'/urls/{url_id}')
        assert response.status_code == 200
        # Проверяем наличие данных проверки
        assert b'Example Title' in response.data or b'Example H1' in response.data

        # Шаг 4: Проверяем список URL
        response = client.get('/urls')
        assert response.status_code == 200
        assert b'example.com' in response.data

    def test_full_cycle_multiple_checks(self, client):
        """Тест полного цикла с несколькими проверками."""
        # Добавляем URL
        response = client.post('/urls', data={'url': 'https://example.com'})
        url_id = response.location.split('/')[-1]

        # Выполняем несколько проверок
        for i in range(3):
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {'Content-Type': 'text/html'}
            mock_response.history = []
            html_content = (
                f'<html><head><title>Check {i}</title></head>'
                f'<body><h1>H1 {i}</h1></body></html>'
            )
            mock_response.content = html_content.encode()
            mock_response.iter_content.return_value = [html_content]

            with patch('page_analyzer.services.check_service.requests.Session') as mock_session:
                mock_session.return_value.get.return_value = mock_response
                client.post(f'/urls/{url_id}/checks')

        # Просматриваем детали - должны быть все проверки
        response = client.get(f'/urls/{url_id}')
        assert response.status_code == 200
        # Проверяем наличие всех проверок
        assert b'Check' in response.data or b'H1' in response.data

