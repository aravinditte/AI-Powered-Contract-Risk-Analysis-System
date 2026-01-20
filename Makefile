.PHONY: help build up down restart logs migrate test

help:
	@echo "Available commands:"
	@echo "  make build      Build all containers"
	@echo "  make up         Start full system"
	@echo "  make down       Stop system"
	@echo "  make restart    Restart system"
	@echo "  make logs       View logs"
	@echo "  make migrate    Run DB migrations"
	@echo "  make test       Run backend tests"

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

restart:
	docker-compose down && docker-compose up -d

logs:
	docker-compose logs -f

migrate:
	docker-compose exec backend alembic upgrade head

test:
	docker-compose exec backend pytest
