from bs4 import BeautifulSoup
from typing import Dict

# Максимальная длина полей в базе данных
MAX_FIELD_LENGTH = 255


def parse(request: str) -> Dict[str, str]:
    """Парсинг HTML для извлечения SEO-данных.

    Args:
        request: HTML-контент страницы.

    Returns:
        dict: Словарь с данными (h1, title, description).
              Все поля обрезаются до MAX_FIELD_LENGTH символов.
    """
    soup = BeautifulSoup(request, 'html.parser')
    data = {}

    h1 = soup.find('h1')
    data['h1'] = (
        h1.get_text().strip()[:MAX_FIELD_LENGTH] if h1 else ''
    )

    title = soup.find('title')
    data['title'] = (
        title.get_text().strip()[:MAX_FIELD_LENGTH] if title else ''
    )

    description = soup.find('meta', attrs={"name": "description"})
    if description is None:
        data['description'] = ''
    else:
        data['description'] = (
            description.get('content', '').strip()[:MAX_FIELD_LENGTH]
        )

    return data
