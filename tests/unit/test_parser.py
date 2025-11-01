"""Тесты для модуля parser."""

import pytest
from page_analyzer.parser import parse, MAX_FIELD_LENGTH


class TestParser:
    """Тесты парсинга HTML."""

    def test_parse_with_all_fields(self):
        """Тест парсинга HTML со всеми полями."""
        html = """
        <html>
        <head>
            <title>Test Title</title>
            <meta name="description" content="Test description">
        </head>
        <body>
            <h1>Test H1</h1>
        </body>
        </html>
        """
        result = parse(html)
        assert result['title'] == 'Test Title'
        assert result['description'] == 'Test description'
        assert result['h1'] == 'Test H1'

    def test_parse_without_h1(self):
        """Тест парсинга HTML без h1."""
        html = """
        <html>
        <head>
            <title>Test Title</title>
        </head>
        <body>
        </body>
        </html>
        """
        result = parse(html)
        assert result['h1'] == ''
        assert result['title'] == 'Test Title'

    def test_parse_without_title(self):
        """Тест парсинга HTML без title."""
        html = """
        <html>
        <body>
            <h1>Test H1</h1>
        </body>
        </html>
        """
        result = parse(html)
        assert result['title'] == ''
        assert result['h1'] == 'Test H1'

    def test_parse_without_description(self):
        """Тест парсинга HTML без description."""
        html = """
        <html>
        <head>
            <title>Test Title</title>
        </head>
        <body>
            <h1>Test H1</h1>
        </body>
        </html>
        """
        result = parse(html)
        assert result['description'] == ''

    def test_parse_empty_html(self):
        """Тест парсинга пустого HTML."""
        html = ""
        result = parse(html)
        assert result['h1'] == ''
        assert result['title'] == ''
        assert result['description'] == ''

    def test_parse_truncates_long_fields(self):
        """Тест обрезки длинных полей."""
        long_text = 'a' * (MAX_FIELD_LENGTH + 100)
        html = f"""
        <html>
        <head>
            <title>{long_text}</title>
        </head>
        <body>
            <h1>{long_text}</h1>
        </body>
        </html>
        """
        result = parse(html)
        assert len(result['title']) == MAX_FIELD_LENGTH
        assert len(result['h1']) == MAX_FIELD_LENGTH

    def test_parse_multiple_h1(self):
        """Тест парсинга HTML с несколькими h1 (берётся первый)."""
        html = """
        <html>
        <body>
            <h1>First H1</h1>
            <h1>Second H1</h1>
        </body>
        </html>
        """
        result = parse(html)
        assert result['h1'] == 'First H1'

    def test_parse_strips_whitespace(self):
        """Тест обрезки пробелов в полях."""
        html = """
        <html>
        <head>
            <title>  Test Title  </title>
        </head>
        <body>
            <h1>  Test H1  </h1>
        </body>
        </html>
        """
        result = parse(html)
        assert result['title'] == 'Test Title'
        assert result['h1'] == 'Test H1'

