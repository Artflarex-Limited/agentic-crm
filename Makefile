.PHONY: help up down build start stop restart logs logs-backend logs-frontend logs-redis logs-postgres migrate seed backup test lint clean ps

COMPOSE_FILE := docker-compose.yml
COMPOSE := docker-compose -f $(COMPOSE_FILE)

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

up: ## Start all services
	$(COMPOSE) up -d

down: ## Stop all services
	$(COMPOSE) down

build: ## Build all images
	$(COMPOSE) build

start: ## Start services (alias for up)
	$(COMPOSE) up -d

stop: ## Stop services
	$(COMPOSE) stop

restart: ## Restart services
	$(COMPOSE) restart

logs: ## View all logs
	$(COMPOSE) logs -f

logs-backend: ## View backend logs
	$(COMPOSE) logs -f backend

logs-frontend: ## View frontend logs
	$(COMPOSE) logs -f frontend

logs-redis: ## View redis logs
	$(COMPOSE) logs -f redis

logs-postgres: ## View postgres logs
	$(COMPOSE) logs -f postgres

logs-celery: ## View celery worker logs
	$(COMPOSE) logs -f celeryworker

migrate: ## Run database migrations
	./scripts/migrate.sh

seed: ## Seed database with sample data
	./scripts/seed.sh

backup: ## Create database backup
	./scripts/backup.sh

test: ## Run tests
	$(COMPOSE) run --rm backend pytest -v

lint: ## Run linters (ruff, black)
	ruff check backend/
	black --check backend/

lint-frontend: ## Run frontend linter
	cd frontend && npm run lint

clean: ## Remove containers, volumes, and images
	$(COMPOSE) down -v --remove-orphans
	docker images 'agentic-crm-*' -q | xargs -r docker rmi -f

ps: ## Show running containers
	$(COMPOSE) ps

worker: ## Start Celery worker (requires worker profile)
	$(COMPOSE) --profile worker up -d celeryworker

worker-logs: ## View celery worker logs
	$(COMPOSE) --profile worker logs -f celeryworker

beat: ## Start Celery beat scheduler (requires worker profile)
	$(COMPOSE) --profile worker up -d celerybeat

deploy: ## Deploy to production
	./scripts/deploy.sh

deploy-staging: ## Deploy to staging
	TAG=staging ./scripts/deploy.sh