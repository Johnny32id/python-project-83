"""Сервис для проверки страниц."""

import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Dict, Any, Optional
from requests.exceptions import (
    RequestException,
    Timeout,
    ConnectionError as RequestsConnectionError,
    HTTPError,
    TooManyRedirects
)
from ..config import config
from ..parser import parse
from ..db import add_check, get_url_by_id

logger = logging.getLogger(__name__)


class CheckService:
    """Сервис для проверки страниц на SEO-пригодность."""

    @staticmethod
    def check_url(url_id: int) -> Dict[str, Any]:
        """Выполнение проверки URL.

        Args:
            url_id: ID URL для проверки.

        Returns:
            dict: Словарь с результатами:
                - success: bool - успешность операции
                - flash_message: str - сообщение для flash
                - flash_category: str - категория flash сообщения
        """
        url = get_url_by_id(url_id)
        if url is None:
            return {
                'success': False,
                'flash_message': 'URL не найден',
                'flash_category': 'alert-danger'
            }

        try:
            # Логируем начало проверки
            logger.info(f'Начало проверки URL ID {url_id}: {url.name}')

            # Создаём сессию для контроля редиректов
            session = requests.Session()
            # Настраиваем адаптер
            adapter = HTTPAdapter(max_retries=Retry(total=0))
            session.mount('http://', adapter)
            session.mount('https://', adapter)

            # Выполнение HTTP-запроса
            logger.debug(f'Выполнение HTTP-запроса к {url.name}')
            response = session.get(
                url.name,
                timeout=(
                    config.REQUEST_CONNECT_TIMEOUT,
                    config.REQUEST_READ_TIMEOUT
                ),
                allow_redirects=True,
                stream=True
            )
            logger.info(
                f'HTTP-запрос к {url.name} выполнен: '
                f'статус {response.status_code}, '
                f'редиректов {len(response.history)}'
            )

            # Проверяем количество редиректов вручную
            if len(response.history) > config.MAX_REDIRECTS:
                raise TooManyRedirects(
                    f'Превышено максимальное количество редиректов: '
                    f'{len(response.history)} > {config.MAX_REDIRECTS}',
                    response=response
                )

            response.raise_for_status()

            # Проверка размера ответа
            content_length = response.headers.get('Content-Length')
            if content_length and int(content_length) > config.MAX_RESPONSE_SIZE:
                return {
                    'success': False,
                    'flash_message': 'Размер ответа слишком большой',
                    'flash_category': 'alert-danger'
                }

            # Чтение содержимого с ограничением размера
            content = CheckService._read_response_content(
                response,
                url.name
            )

            if content is None:
                return {
                    'success': False,
                    'flash_message': (
                        'Размер ответа превышает допустимый лимит'
                    ),
                    'flash_category': 'alert-danger'
                }

            # Проверка Content-Type
            content_type = response.headers.get('Content-Type', '').lower()
            if 'text/html' not in content_type:
                logger.warning(
                    f'Неожиданный Content-Type для {url.name}: '
                    f'{content_type}'
                )

            # Парсинг и сохранение данных
            data = parse(content)
            data['url_id'] = url_id
            data['status_code'] = response.status_code
            add_check(data)

            logger.info(
                f'Успешно выполнена проверка для URL ID {url_id} ({url.name}): '
                f'статус {response.status_code}, '
                f'h1={bool(data.get("h1"))}, '
                f'title={bool(data.get("title"))}, '
                f'description={bool(data.get("description"))}'
            )
            return {
                'success': True,
                'flash_message': 'Страница успешно проверена',
                'flash_category': 'alert-success'
            }

        except Timeout:
            logger.error(f'Таймаут при проверке URL {url.name}')
            return {
                'success': False,
                'flash_message': (
                    'Превышено время ожидания ответа от сервера'
                ),
                'flash_category': 'alert-danger'
            }
        except RequestsConnectionError as e:
            logger.error(f'Ошибка подключения к {url.name}: {str(e)}')
            return {
                'success': False,
                'flash_message': 'Не удалось подключиться к серверу',
                'flash_category': 'alert-danger'
            }
        except TooManyRedirects:
            logger.error(f'Слишком много редиректов для {url.name}')
            return {
                'success': False,
                'flash_message': (
                    'Превышено максимальное количество редиректов'
                ),
                'flash_category': 'alert-danger'
            }
        except HTTPError as e:
            logger.error(f'HTTP ошибка при проверке {url.name}: {str(e)}')
            return {
                'success': False,
                'flash_message': f'Ошибка HTTP: {e.response.status_code}',
                'flash_category': 'alert-danger'
            }
        except RequestException as e:
            logger.error(f'Ошибка запроса к {url.name}: {str(e)}')
            return {
                'success': False,
                'flash_message': 'Произошла ошибка при проверке',
                'flash_category': 'alert-danger'
            }

    @staticmethod
    def _read_response_content(response: requests.Response, url: str) -> Optional[str]:
        """Чтение содержимого ответа с ограничением размера.

        Args:
            response: Объект ответа requests.
            url: URL для логирования.

        Returns:
            str или None: Содержимое ответа или None, если превышен лимит.
        """
        content = ''
        total_size = 0
        try:
            for chunk in response.iter_content(
                chunk_size=8192,
                decode_unicode=True
            ):
                total_size += len(chunk.encode('utf-8'))
                if total_size > config.MAX_RESPONSE_SIZE:
                    logger.warning(
                        f'Превышен размер ответа для {url}: '
                        f'{total_size} байт'
                    )
                    return None
                content += chunk
                if len(content) > config.MAX_RESPONSE_SIZE:
                    logger.warning(
                        f'Превышен размер контента для {url}: '
                        f'{len(content)} символов'
                    )
                    break
            return content
        except Exception as e:
            logger.error(f'Ошибка при чтении ответа от {url}: {str(e)}')
            return None

