"""Тесты безопасности для модуля normalizer."""

import pytest
from page_analyzer.normalizer import normalize


class TestNormalizerSecurity:
    """Тесты безопасности нормализатора."""

    def test_normalize_preserves_scheme(self):
        """Тест сохранения схемы при нормализации."""
        url = "https://example.com/path"
        result = normalize(url)
        assert result.startswith("https://")
        assert not result.endswith("/path")

    def test_normalize_removes_query_params(self):
        """Тест удаления параметров запроса при нормализации."""
        url = "https://example.com/?param=<script>"
        result = normalize(url)
        # Параметры должны быть удалены, скрипты не попадут в БД
        assert result == "https://example.com"
        assert "<script>" not in result

    def test_normalize_removes_fragment(self):
        """Тест удаления фрагмента при нормализации."""
        url = "https://example.com/#malicious"
        result = normalize(url)
        assert result == "https://example.com"
        assert "#malicious" not in result

