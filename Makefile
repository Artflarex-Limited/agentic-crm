.PHONY: help up down build lint test migrate seed logs shell console clean

help:
	@echo "Agentic CRM - Makefile Commands"
	@echo "==============================="
	@echo "make up          - Start all services with docker-compose"
	@echo "make down        - Stop all services"
	@echo "make build       - Build Docker images"
	@echo "make lint        - Run ruff linter"
	@echo "make test        - Run pytest"
	@echo "make migrate     - Run database migrations"
	@echo "make seed        - Seed database with sample data"
	@echo "make logs        - View logs from all services"
	@echo "make shell       - Open a shell in the backend container"
	@echo "make console     - Open Python REPL in backend container"
	@echo "make clean       - Remove containers, volumes, and build artifacts"

up:
	docker compose up --detach

down:
	docker compose down

build:
	docker compose build

lint:
	cd backend && ruff check .

test:
	cd backend && pytest tests/ -v

migrate:
	@./scripts/migrate.sh

seed:
	@./scripts/seed.sh

logs:
	docker compose logs -f

shell:
	docker compose exec backend /bin/bash

console:
	docker compose exec backend python -c "import sys; sys.path.insert(0, '/app'); from app.prisma import prisma; import asyncio; asyncio.run(prisma.connect()); print('Connected to database')"

clean:
	docker compose down -v --rmi local
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf build dist .eggs *.egg-info