from flask import Flask, render_template, request, flash, redirect, url_for
import os
from dotenv import load_dotenv
from .validator import validate
from .normalizer import normalize
from .parser import parse
import requests
from .db import (
    add_url, get_url_by_name,
    get_url_by_id, get_all_urls, add_check, get_checks_by_url_id)

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')


@app.get('/')
def get_index():
    return render_template('form.html'), 200


@app.post('/urls')
def create_url():
    url = request.form.get('url')
    error = validate(url)
    if error:
        flash(error, 'alert-danger')
        return render_template('form.html'), 422
    url = normalize(url)
    url_in_db = get_url_by_name(url)
    if url_in_db:
        url_id = url_in_db.id
        flash('Страница уже существует', 'alert-info')
    else:
        url_id = add_url(url)
        flash('Страница успешно добавлена', 'alert-success')
    return redirect(url_for('get_url', id=url_id))


@app.get('/urls')
def urls_list():
    urls = get_all_urls()
    return render_template('urls_list.html', items=urls), 200


@app.get('/urls/<int:id>')
def get_url(id):
    url = get_url_by_id(id)
    if url is None:
        return render_template('404_page.html'), 404
    checks = get_checks_by_url_id(id)
    return render_template('url_details.html', url=url, checks=checks)


@app.post('/urls/<int:id>/checks')
def add_url_check(id):
    url = get_url_by_id(id)
    try:
        responce = requests.get(url.name)
        responce.raise_for_status()
    except requests.exceptions.RequestException:
        flash('Произошла ошибка при проверке', 'alert-danger')
        return redirect(url_for('get_url', id=id))
    data = parse(responce.text)
    data['url_id'] = id
    data['status_code'] = responce.status_code
    add_check(data)
    flash('Проверка успешна', 'alert-success')
    return redirect(url_for('get_url', id=id))
