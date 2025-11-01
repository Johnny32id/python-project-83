"""Тесты для модуля validator."""

import pytest
from page_analyzer.validator import validate, MAX_URL_LENGTH


class TestValidator:
    """Тесты валидации URL."""

    def test_validate_empty_url(self):
        """Тест валидации пустого URL."""
        result = validate('')
        assert result == 'Поле URL не должно быть пустым.'

    def test_validate_none_url(self):
        """Тест валидации None URL."""
        result = validate(None)
        assert result == 'Поле URL не должно быть пустым.'

    def test_validate_too_long_url(self):
        """Тест валидации слишком длинного URL."""
        long_url = 'https://example.com/' + 'a' * MAX_URL_LENGTH
        result = validate(long_url)
        assert 'Длина URL превышает' in result

    def test_validate_invalid_url(self):
        """Тест валидации некорректного URL."""
        result = validate('not-a-valid-url')
        assert result == 'Некорректный URL'

    def test_validate_valid_url(self):
        """Тест валидации корректного URL."""
        result = validate('https://example.com')
        assert result is None

    def test_validate_valid_url_with_path(self):
        """Тест валидации корректного URL с путём."""
        result = validate('https://example.com/path/to/page')
        assert result is None

    def test_validate_valid_url_with_query(self):
        """Тест валидации корректного URL с параметрами."""
        result = validate('https://example.com?param=value')
        assert result is None

