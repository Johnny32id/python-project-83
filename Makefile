install:
		poetry install

setup:
		make install
		sh ./build.sh

dev:
		poetry run flask --app page_analyzer:app run

PORT ?= 8000
start:
		poetry run gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app

lint:
		poetry run flake8 page_analyzer/

test:
		poetry run pytest tests/ -v

test-cov:
		poetry run pytest tests/ -v --cov=page_analyzer --cov-report=term-missing