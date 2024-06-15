from flask import Flask, render_template, request, flash, redirect, url_for
import os
from dotenv import load_dotenv
from .validator import validate
from .normalizer import normalize
from .db import add_url, get_url_by_name, get_url_by_id, get_all_urls

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')


@app.get('/')
def get_index():
    return render_template('index.html'), 200


@app.post('/urls')
def create_url():
    url = request.form.get('url')
    error = validate(url)
    if error:
        flash(error, 'alert-danger')
        return render_template('index.html'), 422
    url = normalize(url)
    url_in_db = get_url_by_name(url)
    if url_in_db:
        url_id = url_in_db.id
        flash('Страница уже существует', 'alert-info')
    else:
        url_id = add_url(url)
        flash('Страница успешно добавлена', 'alert-success')
    return redirect(url_for('get_url', url_id=url_id))


@app.get('/urls')
def urls_list():
    urls = get_all_urls()
    return render_template('urls_list.html', items=urls), 200


@app.get('/urls/url<int:url_id>')
def get_url(url_id):
    url = get_url_by_id(url_id)
    if url is None:
        return render_template('404_page.html'), 404
    return render_template('url_details.html', url=url)
