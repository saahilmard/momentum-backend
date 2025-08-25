.PHONY: up down migrate seed test lint format clean

# Development commands
up:
	docker-compose up -d

down:
	docker-compose down

migrate:
	docker-compose exec api alembic upgrade head

seed:
	docker-compose exec api python -m app.scripts.seed

test:
	docker-compose exec api pytest -v --cov=app

lint:
	docker-compose exec api ruff check app tests
	docker-compose exec api mypy app

format:
	docker-compose exec api black app tests
	docker-compose exec api ruff format app tests

clean:
	docker-compose down -v
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

# Risk scoring
risk-score:
	docker-compose exec api python -m app.jobs.risk_scoring

# Database
db-reset:
	docker-compose down -v
	docker-compose up -d postgres redis
	sleep 5
	docker-compose exec api alembic upgrade head
	docker-compose exec api python -m app.scripts.seed

# Logs
logs:
	docker-compose logs -f api

# Shell
shell:
	docker-compose exec api python -c "from app.database import engine; import asyncio; asyncio.run(engine.dispose())" 