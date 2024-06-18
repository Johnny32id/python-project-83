from bs4 import BeautifulSoup


def parse(request):
    soup = BeautifulSoup(request, 'html.parser')
    data = {}
    h1 = soup.find('h1')
    data['h1'] = h1.get_text().strip() if h1 else ''
    title = soup.find('title')
    data['title'] = title.get_text().strip() if title else ''
    description = soup.find('meta', attrs={"name": "description"})
    if description is None:
        data['description'] = ''
    else:
        data['description'] = description.get('content', '').strip()
    return data
