# Convenience wrappers around the common dev workflows.
# Usage: `make up`, `make test`, etc.

.PHONY: up down logs migrate test lint fmt

up:            ## Build and start the full stack
	docker compose up --build

down:          ## Stop and remove containers
	docker compose down

logs:          ## Tail all service logs
	docker compose logs -f

migrate:       ## Apply DB migrations inside the backend container
	docker compose exec backend alembic upgrade head

test:          ## Run backend + frontend test suites
	cd backend && pytest -q
	cd frontend && npm test --silent

lint:          ## Lint both apps
	cd backend && ruff check . && mypy app
	cd frontend && npm run lint

fmt:           ## Auto-format both apps
	cd backend && ruff format .
	cd frontend && npm run format
