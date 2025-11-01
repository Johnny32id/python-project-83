import validators
from typing import Optional

MAX_URL_LENGTH = 255


def validate(url: Optional[str]) -> Optional[str]:
    """Валидация URL.

    Args:
        url: URL для валидации.

    Returns:
        str или None: Сообщение об ошибке или None, если валидация прошла.
    """
    if not url:
        return 'Поле URL не должно быть пустым.'
    elif len(url) > MAX_URL_LENGTH:
        return f'Длина URL превышает {MAX_URL_LENGTH} символов.'
    elif not validators.url(url):
        return 'Некорректный URL'
    return None
