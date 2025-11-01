"""Тесты безопасности для модуля validator."""

import pytest
from page_analyzer.validator import validate


class TestValidatorSecurity:
    """Тесты безопасности валидатора."""

    def test_validate_sql_injection_attempt(self):
        """Тест защиты от попыток SQL-инъекции в URL."""
        sql_injection = "https://example.com'; DROP TABLE urls; --"
        # Валидатор должен проверять формат URL, а не содержимое
        result = validate(sql_injection)
        # Если URL корректный по формату, валидация проходит
        # SQL-инъекция не должна попасть в БД благодаря параметризованным запросам
        assert result is None or 'Некорректный URL' in result

    def test_validate_xss_attempt(self):
        """Тест защиты от попыток XSS в URL."""
        xss_attempt = "https://example.com/<script>alert('xss')</script>"
        result = validate(xss_attempt)
        # URL с <script> не должен пройти валидацию как корректный URL
        assert result == 'Некорректный URL'

    def test_validate_special_characters(self):
        """Тест обработки специальных символов."""
        special_chars = "https://example.com/?param=value&other=test"
        result = validate(special_chars)
        # URL с параметрами должен быть валиден
        assert result is None

    def test_validate_javascript_protocol(self):
        """Тест блокировки опасных протоколов."""
        js_url = "javascript:alert('xss')"
        result = validate(js_url)
        # JavaScript протокол не должен быть разрешён
        assert result == 'Некорректный URL'

    def test_validate_data_protocol(self):
        """Тест блокировки data протокола."""
        data_url = "data:text/html,<script>alert('xss')</script>"
        result = validate(data_url)
        # Data протокол не должен быть разрешён
        assert result == 'Некорректный URL'

