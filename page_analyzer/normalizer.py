from urllib.parse import urlparse


def normalize(url):
    data = urlparse(url)
    return f'{data.scheme}://{data.netloc}'
