PYTHON ?= python
COMPOSE ?= docker compose

.PHONY: help install lint typecheck test up down logs migrate health seed

help:
	@echo "install     — venv + зависимости (локально)"
	@echo "lint        — ruff"
	@echo "typecheck   — mypy"
	@echo "test        — pytest"
	@echo "up          — Docker Compose"
	@echo "down        — остановить стек"
	@echo "logs        — логи web и bot"
	@echo "migrate     — alembic upgrade head (локально)"
	@echo "seed        — демо-данные"

install:
	$(PYTHON) -m venv .venv
	.venv/bin/pip install -e ".[dev]" || .venv/Scripts/pip install -e ".[dev]"

lint:
	ruff check app tests
	ruff format --check app tests

typecheck:
	mypy app

test:
	pytest -q

up:
	$(COMPOSE) up --build -d

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f web bot

migrate:
	alembic upgrade head

health:
	curl -sf http://localhost:8000/health && echo
	curl -sf http://localhost:8000/health/ready && echo

seed:
	$(COMPOSE) exec web python -m app.db.seed
