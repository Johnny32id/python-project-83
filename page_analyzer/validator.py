import validators

MAX_URL_LENGTH = 255


def validate(url):
    if not url:
        return 'Поле URL не должно быть пустым.'
    elif len(url) > MAX_URL_LENGTH:
        return f'Длина URL превышает {MAX_URL_LENGTH} символов.'
    elif not validators.url(url):
        return 'Некорректный URL'
