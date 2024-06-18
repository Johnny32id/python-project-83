import os
from datetime import datetime
from dotenv import load_dotenv
from psycopg2 import connect
from psycopg2.extras import NamedTupleCursor

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')


class DatabaseConnection:
    def __enter__(self):
        self.connection = connect(DATABASE_URL)
        self.cursor = self.connection.cursor(cursor_factory=NamedTupleCursor)
        return self.cursor

    def __exit__(self, exc_type, exc_value, traceback):
        self.cursor.close()
        self.connection.commit()
        self.connection.close()


def add_url(url):
    with DatabaseConnection() as cursor:
        query = ('INSERT INTO urls (name, created_at) VALUES (%s, %s) '
                 'RETURNING id')
        values = (url, datetime.now())
        cursor.execute(query, values)
        return cursor.fetchone().id


def get_url_by_name(url):
    with DatabaseConnection() as cursor:
        query = ('SELECT * FROM urls WHERE name = (%s)')
        cursor.execute(query, (url, ))
        return cursor.fetchone()


def get_url_by_id(id):
    with DatabaseConnection() as cursor:
        query = (f'SELECT * FROM urls WHERE id = {id}')
        cursor.execute(query)
        return cursor.fetchone()


def get_all_urls():
    with DatabaseConnection() as cursor:
        query_urls = 'SELECT id, name FROM urls ORDER BY id DESC;'
        query_checks = ('SELECT url_id,'
                        ' status_code, MAX(created_at) AS last_check'
                        ' FROM url_checks GROUP BY url_id, status_code'
                        ' ORDER BY last_check;')
        cursor.execute(query_urls)
        all_urls = cursor.fetchall()
        cursor.execute(query_checks)
        checks = {data.url_id: data for data in cursor.fetchall()}
        urls = []
        for url in all_urls:
            url_data = {
                'id': url.id,
                'name': url.name,
            }
            if check := checks.get(url.id):
                url_data['status_code'] = check.status_code
                url_data['last_check'] = check.last_check
            urls.append(url_data)
        return urls


def add_check(data):
    with DatabaseConnection() as cursor:
        query = ('INSERT INTO url_checks '
                 '(url_id, status_code, h1, title, description, created_at) '
                 'VALUES (%s, %s, %s, %s, %s, %s)')
        values = (data.get('url_id'), data.get('status_code'),
                  data.get('h1'), data.get('title'), data.get('description'),
                  datetime.now())
        cursor.execute(query, values)


def get_checks_by_url_id(id):
    with DatabaseConnection() as cursor:
        query = (f'SELECT * FROM url_checks WHERE url_id = {id}'
                 ' ORDER BY id DESC')
        cursor.execute(query)
        return cursor.fetchall()
