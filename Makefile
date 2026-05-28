.PHONY: help build up down logs migrate restart

help:
	@echo "Available commands:"
	@echo "  make build     - Build all Docker images"
	@echo "  make up        - Start all services"
	@echo "  make down      - Stop all services"
	@echo "  make logs      - View logs"
	@echo "  make migrate   - Run database migrations"
	@echo "  make restart   - Restart all services"

build:
	docker-compose build --no-cache

up:
	docker-compose up -d
	@echo "✅ Aetherion started. API: http://localhost:8000/docs | UI: http://localhost:3000"

down:
	docker-compose down -v

logs:
	docker-compose logs -f

migrate:
	docker-compose exec gateway alembic upgrade head

restart: down up