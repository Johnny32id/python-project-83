from flask import (
    Flask,
    render_template,
    request,
    flash,
    redirect,
    url_for,
    Response
)
import logging
from typing import Tuple, Union
from .config import config
from .services import URLService, CheckService

logger = logging.getLogger(__name__)

# Валидация конфигурации при импорте
try:
    config.validate()
except ValueError as e:
    logger.error(f'Ошибка конфигурации: {str(e)}')
    raise

app = Flask(__name__)
app.config['SECRET_KEY'] = config.get_secret_key()


@app.get('/')
def get_index() -> Tuple[str, int]:
    """Главная страница с формой добавления URL.

    Returns:
        Tuple[str, int]: HTML шаблон и HTTP статус код.
    """
    return render_template('form.html'), 200


@app.post('/urls')
def create_url() -> Union[Response, Tuple[str, int]]:
    """Создание нового URL.

    Returns:
        Response или Tuple[str, int]: Редирект на страницу URL или
        форма с ошибкой и HTTP статус код.
    """
    url_input = request.form.get('url')
    result = URLService.create_url(url_input)

    if not result['success']:
        flash(result['flash_message'], result['flash_category'])
        return render_template('form.html'), 422

    flash(result['flash_message'], result['flash_category'])
    return redirect(url_for('get_url', id=result['url_id']))


@app.get('/urls')
def urls_list() -> Tuple[str, int]:
    """Список всех URL с последними проверками.

    Returns:
        Tuple[str, int]: HTML шаблон со списком URL и HTTP статус код.
    """
    urls = URLService.get_all_urls()
    return render_template('urls_list.html', urls=urls), 200


@app.get('/urls/<int:id>')
def get_url(id: int) -> Tuple[str, int]:
    """Страница детальной информации об URL.

    Args:
        id: ID URL.

    Returns:
        Tuple[str, int]: HTML шаблон с деталями URL и HTTP статус код.
    """
    url = URLService.get_url(id)
    if url is None:
        return render_template('404_page.html'), 404
    checks = URLService.get_url_checks(id)
    return render_template('url_details.html', url=url, checks=checks)


@app.post('/urls/<int:id>/checks')
def add_url_check(id: int) -> Response:
    """Добавление проверки для указанного URL.

    Args:
        id: ID URL для проверки.

    Returns:
        Response: Редирект на страницу URL.
    """
    result = CheckService.check_url(id)

    if not result['success'] and result['flash_message'] == 'URL не найден':
        return redirect(url_for('urls_list'))

    flash(result['flash_message'], result['flash_category'])
    return redirect(url_for('get_url', id=id))
