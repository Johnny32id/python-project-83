from flask import Flask, render_template
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')


@app.get('/')
def get_index():
    return render_template('index.html'), 200
