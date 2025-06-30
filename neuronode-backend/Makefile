.PHONY: help install dev test lint format clean docker-build docker-up docker-down

help:
    @echo "Available commands:"
    @echo "  install      Install dependencies"
    @echo "  dev          Run development server"
    @echo "  test         Run tests"
    @echo "  lint         Run linters"
    @echo "  format       Format code"
    @echo "  clean        Clean up files"
    @echo "  docker-build Build Docker images"
    @echo "  docker-up    Start Docker services"
    @echo "  docker-down  Stop Docker services"

install:
    pip install -r requirements.txt
    pip install -r requirements-dev.txt

dev:
    uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8080

test:
    pytest tests/ -v --cov=src

lint:
    flake8 src/
    mypy src/
    black --check src/

format:
    black src/
    isort src/

clean:
    find . -type f -name "*.pyc" -delete
    find . -type d -name "__pycache__" -delete
    find . -type d -name ".pytest_cache" -delete
    find . -type d -name ".mypy_cache" -delete

docker-build:
    docker-compose build

docker-up:
    docker-compose up -d

docker-down:
    docker-compose down

docker-logs:
    docker-compose logs -f

# Database commands
neo4j-backup:
    docker exec ki-wissenssystem-neo4j neo4j-admin database dump neo4j --to-path=/backups

neo4j-restore:
    docker exec ki-wissenssystem-neo4j neo4j-admin database load neo4j --from-path=/backups

# CLI shortcuts
query:
    python -m src.cli query "$(QUERY)"

process-doc:
    python -m src.cli process "$(DOC)"

stats:
    python -m src.cli stats