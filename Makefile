all: format lint mypy test

install:
	poetry install

format:
	poetry run black src alembic

lint:
	poetry run flake8 src alembic

mypy:
	poetry run mypy --strict src alembic

clean-db:
	rm local.db 2> /dev/null || true

test: clean-db
	poetry run pytest -sv .

coverage: clean-db
	poetry run pytest --cov . --cov-report xml

run: install
	poetry run uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload
