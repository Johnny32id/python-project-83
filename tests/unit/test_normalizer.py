"""Тесты для модуля normalizer."""

import pytest
from page_analyzer.normalizer import normalize


class TestNormalizer:
    """Тесты нормализации URL."""

    def test_normalize_simple_url(self):
        """Тест нормализации простого URL."""
        url = 'https://example.com'
        result = normalize(url)
        assert result == 'https://example.com'

    def test_normalize_url_with_path(self):
        """Тест нормализации URL с путём."""
        url = 'https://example.com/path/to/page'
        result = normalize(url)
        assert result == 'https://example.com'

    def test_normalize_url_with_query(self):
        """Тест нормализации URL с параметрами."""
        url = 'https://example.com?param=value'
        result = normalize(url)
        assert result == 'https://example.com'

    def test_normalize_url_with_fragment(self):
        """Тест нормализации URL с якорем."""
        url = 'https://example.com#section'
        result = normalize(url)
        assert result == 'https://example.com'

    def test_normalize_url_with_all(self):
        """Тест нормализации URL со всеми компонентами."""
        url = 'https://example.com/path?param=value#section'
        result = normalize(url)
        assert result == 'https://example.com'

    def test_normalize_url_with_port(self):
        """Тест нормализации URL с портом."""
        url = 'https://example.com:8080/path'
        result = normalize(url)
        assert result == 'https://example.com:8080'

    def test_normalize_http_url(self):
        """Тест нормализации HTTP URL."""
        url = 'http://example.com/path'
        result = normalize(url)
        assert result == 'http://example.com'

