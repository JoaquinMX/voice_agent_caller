.PHONY: format lint up down logs deps

format:
	python -m ruff format services

lint:
	python -m ruff check services

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f

deps:
	source venv/bin/activate && pip install ruff pytest
