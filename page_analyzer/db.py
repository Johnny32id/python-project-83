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
        values = (url, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        cursor.execute(query, values)
        return cursor.fetchone().id


def get_url_by_name(url):
    with DatabaseConnection() as cursor:
        query = ('SELECT * FROM urls WHERE name = (%s)')
        cursor.execute(query, (url, ))
        return cursor.fetchone()


def get_url_by_id(url_id):
    with DatabaseConnection() as cursor:
        query = ('SELECT * FROM urls WHERE id = (%s)')
        cursor.execute(query, (url_id, ))
        return cursor.fetchone()


def get_all_urls():
    with DatabaseConnection() as cursor:
        query_urls = 'SELECT id, name FROM urls ORDER BY id DESC;'
        cursor.execute(query_urls)
        all_urls = cursor.fetchall()
        urls = []
        for url in all_urls:
            url_data = {
                'id': url.id,
                'name': url.name,
            }
            urls.append(url_data)
        return urls
