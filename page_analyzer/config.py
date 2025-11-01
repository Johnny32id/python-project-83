"""Модуль конфигурации приложения."""

import os
import secrets
import logging
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class Config:
    """Класс для управления конфигурацией приложения."""

    # Настройки базы данных
    DATABASE_URL: Optional[str] = os.getenv('DATABASE_URL')
    DB_RETRIES: int = int(os.getenv('DB_RETRIES', '3'))

    # Настройки Flask
    # SECRET_KEY используется для подписывания сессий и flash-сообщений
    SECRET_KEY: Optional[str] = os.getenv('SECRET_KEY')

    # Настройки HTTP-запросов
    REQUEST_CONNECT_TIMEOUT: int = int(
        os.getenv('REQUEST_CONNECT_TIMEOUT', '5')
    )
    REQUEST_READ_TIMEOUT: int = int(
        os.getenv('REQUEST_READ_TIMEOUT', '30')
    )
    # 10 МБ
    MAX_RESPONSE_SIZE: int = int(
        os.getenv('MAX_RESPONSE_SIZE', '10485760')
    )
    MAX_REDIRECTS: int = int(os.getenv('MAX_REDIRECTS', '10'))

    @classmethod
    def validate(cls) -> None:
        """Валидация обязательных переменных окружения.

        Raises:
            ValueError: Если обязательные переменные не заданы.
        """
        required_vars = {
            'DATABASE_URL': cls.DATABASE_URL,
        }

        missing_vars = [
            var for var, value in required_vars.items() if not value
        ]

        if missing_vars:
            error_msg = (
                f'Отсутствуют обязательные переменные окружения: '
                f'{", ".join(missing_vars)}'
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Генерируем SECRET_KEY автоматически, если не задан
        if not cls.SECRET_KEY:
            cls.SECRET_KEY = secrets.token_urlsafe(32)
            logger.warning(
                'SECRET_KEY не задан. Сгенерирован автоматически. '
                'Для production рекомендуется задать SECRET_KEY вручную.'
            )

        logger.info('Конфигурация успешно проверена')

    @classmethod
    def get_database_url(cls) -> str:
        """Получение URL базы данных.

        Returns:
            str: URL базы данных.

        Raises:
            ValueError: Если DATABASE_URL не задан.
        """
        if not cls.DATABASE_URL:
            raise ValueError('DATABASE_URL не задан в переменных окружения')
        return cls.DATABASE_URL

    @classmethod
    def get_secret_key(cls) -> str:
        """Получение секретного ключа Flask.

        Возвращает SECRET_KEY из переменных окружения или автоматически
        сгенерированный ключ. Ключ используется для:
        - Подписывания flash-сообщений (уведомления пользователю)
        - Подписывания cookies сессий Flask
        - Защиты от подделки данных

        Returns:
            str: Секретный ключ.
        """
        if not cls.SECRET_KEY:
            cls.SECRET_KEY = secrets.token_urlsafe(32)
            logger.warning(
                'SECRET_KEY не задан. '
                'Сгенерирован автоматически для разработки.'
            )
        return cls.SECRET_KEY


# Создаем экземпляр конфигурации
config = Config()
