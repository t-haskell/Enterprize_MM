.PHONY: bootstrap up down seed train predict test fmt lint build release

bootstrap:
	pip install pre-commit || true
	pre-commit install
	cp -n .env.example .env || true
	cp -n services/serving/.env.example services/serving/.env || true
	cp -n services/api/.env.example services/api/.env || true

up:
	docker compose up -d --build

down:
	docker compose down -v

seed:
	docker compose exec db psql -U mm_user -d market_magic -f /docker-entrypoint-initdb.d/01_schema.sql

train:
	docker compose exec modeling python -m modeling.train

predict:
	curl -s http://localhost:8080/predict -X POST -H "Content-Type: application/json" -d '{"symbol":"AAPL"}' | jq

test:
	docker compose exec modeling pytest -q

fmt:
	docker compose exec modeling ruff format .
	docker compose exec modeling ruff check --fix .
	docker compose exec modeling mypy modeling || true

build:
	docker compose build

release:
	@echo "Handled by GitHub Actions / Jenkins"
