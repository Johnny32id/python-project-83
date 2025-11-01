import logging
import time
from datetime import datetime
from typing import Optional, List, Dict, Any
from psycopg2 import connect, Error as DBError
from psycopg2.extras import NamedTupleCursor
from .config import config

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Контекстный менеджер для работы с подключением к базе данных."""

    def __init__(self, retries: Optional[int] = None) -> None:
        """
        Инициализация менеджера подключения.

        Args:
            retries: Количество попыток переподключения при ошибке.
                    Если не указано, используется значение из конфигурации.
        """
        self.retries = retries if retries is not None else config.DB_RETRIES
        self.connection: Optional[Any] = None
        self.cursor: Optional[Any] = None

    def __enter__(self) -> Any:
        """Открытие подключения к базе данных с обработкой ошибок."""
        last_exception = None
        for attempt in range(self.retries):
            try:
                self.connection = connect(config.get_database_url())
                self.cursor = self.connection.cursor(
                    cursor_factory=NamedTupleCursor
                )
                return self.cursor
            except DBError as e:
                last_exception = e
                attempt_num = attempt + 1
                logger.error(
                    f'Ошибка подключения к БД '
                    f'(попытка {attempt_num}/{self.retries}): {str(e)}'
                )
                if attempt < self.retries - 1:
                    time.sleep(0.5 * (attempt + 1))
                else:
                    error_msg = (
                        f'Не удалось подключиться к БД '
                        f'после {self.retries} попыток'
                    )
                    raise ConnectionError(error_msg) from last_exception
        return None

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_value: Optional[BaseException],
        traceback: Optional[Any]
    ) -> None:
        """Закрытие подключения с обработкой ошибок транзакций."""
        if self.cursor:
            try:
                self.cursor.close()
            except DBError as e:
                logger.error(f'Ошибка при закрытии курсора: {str(e)}')

        if self.connection:
            try:
                if exc_type is None:
                    # Коммитим только если не было исключений
                    self.connection.commit()
                else:
                    # Откатываем транзакцию при ошибке
                    self.connection.rollback()
                    logger.error(
                        f'Откат транзакции из-за ошибки: '
                        f'{exc_type.__name__}: {exc_value}'
                    )
            except DBError as e:
                logger.error(f'Ошибка при коммите/откате транзакции: {str(e)}')
            finally:
                try:
                    self.connection.close()
                except DBError as e:
                    logger.error(f'Ошибка при закрытии подключения: {str(e)}')


def add_url(url: str) -> int:
    """Добавление нового URL в базу данных.

    Args:
        url: URL для добавления.

    Returns:
        int: ID добавленного URL.

    Raises:
        DBError: При ошибке выполнения запроса к БД.
    """
    try:
        with DatabaseConnection() as cursor:
            query = ('INSERT INTO urls (name, created_at) VALUES (%s, %s) '
                     'RETURNING id')
            values = (url, datetime.now())
            cursor.execute(query, values)
            return cursor.fetchone().id
    except DBError as e:
        logger.error(f'Ошибка при добавлении URL {url}: {str(e)}')
        raise


def get_url_by_name(url: str) -> Optional[Any]:
    """Получение URL по имени.

    Args:
        url: URL для поиска.

    Returns:
        NamedTuple или None: Найденный URL или None.

    Raises:
        DBError: При ошибке выполнения запроса к БД.
    """
    try:
        with DatabaseConnection() as cursor:
            query = ('SELECT * FROM urls WHERE name = (%s)')
            cursor.execute(query, (url, ))
            return cursor.fetchone()
    except DBError as e:
        logger.error(f'Ошибка при поиске URL {url}: {str(e)}')
        raise


def get_url_by_id(id: int) -> Optional[Any]:
    """Получение URL по ID.

    Args:
        id: ID URL для поиска.

    Returns:
        NamedTuple или None: Найденный URL или None.

    Raises:
        DBError: При ошибке выполнения запроса к БД.
    """
    try:
        with DatabaseConnection() as cursor:
            query = ('SELECT * FROM urls WHERE id = %s')
            cursor.execute(query, (id, ))
            return cursor.fetchone()
    except DBError as e:
        logger.error(f'Ошибка при получении URL по ID {id}: {str(e)}')
        raise


def get_all_urls() -> List[Any]:
    """Получение списка всех URL с последними проверками.

    Returns:
        list: Список URL с информацией о последней проверке.

    Raises:
        DBError: При ошибке выполнения запроса к БД.
    """
    try:
        with DatabaseConnection() as cursor:
            # Оптимизированный запрос с подзапросом для последней проверки
            query = ("""
                SELECT
                    urls.id,
                    urls.name,
                    latest_check.status_code,
                    latest_check.created_at AS last_check
                FROM urls
                LEFT JOIN LATERAL (
                    SELECT status_code, created_at
                    FROM url_checks
                    WHERE url_checks.url_id = urls.id
                    ORDER BY created_at DESC
                    LIMIT 1
                ) AS latest_check ON true
                ORDER BY urls.id DESC
            """)
            cursor.execute(query)
            return cursor.fetchall()
    except DBError as e:
        logger.error(f'Ошибка при получении списка URL: {str(e)}')
        raise


def add_check(data: Dict[str, Any]) -> None:
    """Добавление новой проверки URL в базу данных.

    Args:
        data: Словарь с данными проверки (url_id, status_code, h1,
              title, description).

    Raises:
        DBError: При ошибке выполнения запроса к БД.
    """
    try:
        with DatabaseConnection() as cursor:
            query = ('INSERT INTO url_checks '
                     '(url_id, status_code, h1, title, description, '
                     'created_at) VALUES (%s, %s, %s, %s, %s, %s)')
            values = (
                data.get('url_id'),
                data.get('status_code'),
                data.get('h1'),
                data.get('title'),
                data.get('description'),
                datetime.now()
            )
            cursor.execute(query, values)
            url_id = data.get('url_id')
            logger.info(f'Добавлена проверка для URL ID {url_id}')
    except DBError as e:
        url_id = data.get('url_id', 'неизвестен')
        logger.error(f'Ошибка при добавлении проверки для URL ID {url_id}: '
                     f'{str(e)}')
        raise


def get_last_check_by_url_id(id: int) -> Optional[Any]:
    """Получение последней проверки для указанного URL.

    Args:
        id: ID URL.

    Returns:
        NamedTuple или None: Последняя проверка для URL или None.

    Raises:
        DBError: При ошибке выполнения запроса к БД.
    """
    try:
        with DatabaseConnection() as cursor:
            query = ('SELECT * FROM url_checks WHERE url_id = %s'
                     ' ORDER BY created_at DESC, id DESC LIMIT 1')
            cursor.execute(query, (id, ))
            return cursor.fetchone()
    except DBError as e:
        logger.error(
            f'Ошибка при получении последней проверки для URL ID {id}: '
            f'{str(e)}'
        )
        raise


def get_checks_by_url_id(id: int) -> List[Any]:
    """Получение всех проверок для указанного URL.

    Args:
        id: ID URL.

    Returns:
        list: Список проверок для URL.

    Raises:
        DBError: При ошибке выполнения запроса к БД.
    """
    try:
        with DatabaseConnection() as cursor:
            query = ('SELECT * FROM url_checks WHERE url_id = %s'
                     ' ORDER BY created_at DESC, id DESC')
            cursor.execute(query, (id, ))
            return cursor.fetchall()
    except DBError as e:
        logger.error(f'Ошибка при получении проверок для URL ID {id}: '
                     f'{str(e)}')
        raise
