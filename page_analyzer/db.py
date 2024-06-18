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
        query = ('SELECT urls.id, urls.name,'
                 ' checks.status_code,'
                 ' MAX(checks.created_at) AS last_check FROM urls'
                 ' LEFT JOIN url_checks AS checks'
                 ' ON urls.id = checks.url_id'
                 ' GROUP BY urls.id, status_code'
                 ' ORDER BY urls.id DESC;')
        cursor.execute(query)
        return cursor.fetchall()


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
