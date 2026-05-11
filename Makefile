.PHONY: all
all: install fmt test

.PHONY: dev
dev:
	poetry run uvicorn app.main:create_app --factory --reload

.PHONY: fmt
fmt:
	poetry run ruff format .
	poetry run ruff check . --fix
	poetry run mypy .
	poetry run ruff check .

.PHONY: install
install:
	poetry install

.PHONY: test
test:
	poetry run pytest -vv
