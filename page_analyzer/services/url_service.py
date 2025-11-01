"""Сервис для работы с URL."""

import logging
from typing import Optional, Dict, Any
from ..validator import validate
from ..normalizer import normalize
from ..db import (
    add_url,
    get_url_by_name,
    get_url_by_id,
    get_all_urls,
    get_checks_by_url_id
)

logger = logging.getLogger(__name__)


class URLService:
    """Сервис для управления URL."""

    @staticmethod
    def create_url(url_input: Optional[str]) -> Dict[str, Any]:
        """Создание нового URL с валидацией и нормализацией.

        Args:
            url_input: Входной URL для обработки.

        Returns:
            dict: Словарь с результатами:
                - success: bool - успешность операции
                - url_id: int или None - ID созданного или найденного URL
                - error: str или None - сообщение об ошибке
                - flash_message: str или None - сообщение для flash
                - flash_category: str или None - категория flash сообщения
        """
        error = validate(url_input)
        if error:
            return {
                'success': False,
                'url_id': None,
                'error': error,
                'flash_message': error,
                'flash_category': 'alert-danger'
            }

        normalized_url = normalize(url_input)
        logger.debug(f'Нормализованный URL: {normalized_url}')
        url_in_db = get_url_by_name(normalized_url)

        if url_in_db:
            logger.info(
                f'URL уже существует: {normalized_url} (ID: {url_in_db.id})'
            )
            return {
                'success': True,
                'url_id': url_in_db.id,
                'error': None,
                'flash_message': 'Страница уже существует',
                'flash_category': 'alert-info'
            }

        try:
            url_id = add_url(normalized_url)
            logger.info(f'Добавлен новый URL: {normalized_url} (ID: {url_id})')
            return {
                'success': True,
                'url_id': url_id,
                'error': None,
                'flash_message': 'Страница успешно добавлена',
                'flash_category': 'alert-success'
            }
        except Exception as e:
            logger.error(f'Ошибка при добавлении URL {normalized_url}: {str(e)}')
            return {
                'success': False,
                'url_id': None,
                'error': 'Произошла ошибка при добавлении URL',
                'flash_message': 'Произошла ошибка при добавлении URL',
                'flash_category': 'alert-danger'
            }

    @staticmethod
    def get_url(id: int) -> Optional[Any]:
        """Получение URL по ID.

        Args:
            id: ID URL.

        Returns:
            NamedTuple или None: Найденный URL или None.
        """
        return get_url_by_id(id)

    @staticmethod
    def get_all_urls() -> list:
        """Получение списка всех URL с последними проверками.

        Returns:
            list: Список URL с информацией о последней проверке.
        """
        return get_all_urls()

    @staticmethod
    def get_url_checks(id: int) -> list:
        """Получение всех проверок для URL.

        Args:
            id: ID URL.

        Returns:
            list: Список проверок для URL.
        """
        return get_checks_by_url_id(id)

