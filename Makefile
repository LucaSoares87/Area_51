.PHONY: help install dev run test test-cov lint format type-check clean docker-build docker-up docker-down docker-dev docker-logs

help:
	@echo ""
	@echo "  Identificacao Aerea - Comandos disponiveis"
	@echo "  ==========================================="
	@echo ""
	@echo "  make install        instala dependencias de producao"
	@echo "  make dev            instala dependencias de desenvolvimento"
	@echo "  make run            sobe a API com hot reload"
	@echo "  make test           executa os testes"
	@echo "  make test-cov       executa testes com relatorio de cobertura"
	@echo "  make lint           verifica estilo do codigo (ruff)"
	@echo "  make format         formata o codigo automaticamente"
	@echo "  make type-check     verificacao estatica de tipos (mypy)"
	@echo "  make clean          remove artefatos temporarios"
	@echo "  make docker-build   builda a imagem docker"
	@echo "  make docker-up      sobe containers de producao"
	@echo "  make docker-down    derruba containers"
	@echo "  make docker-dev     sobe containers de desenvolvimento"
	@echo "  make docker-logs    exibe logs em tempo real"
	@echo ""

install:
	pip install --upgrade pip
	pip install -r requirements.txt

dev:
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

run:
	uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload

test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html

lint:
	ruff check src/ tests/

format:
	ruff format src/ tests/

type-check:
	mypy src/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name .mypy_cache -exec rm -rf {} +
	find . -type d -name .ruff_cache -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf htmlcov/
	rm -rf .coverage

docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-dev:
	docker compose -f docker-compose.dev.yml up --build

docker-logs:
	docker compose logs -f

run-aerial:
	python -m uvicorn src.aerial_housing_detection.api.main:app --host 0.0.0.0 --port 8000 --reload

test-aerial:
	python -m pytest tests/test_api tests/test_pipeline tests/test_reports -v

lint-aerial:
	python -m ruff check config src/aerial_housing_detection tests/test_api tests/test_pipeline tests/test_reports

format-aerial:
	python -m ruff format config src/aerial_housing_detection tests/test_api tests/test_pipeline tests/test_reports

compile-aerial:
	python -m compileall config src/aerial_housing_detection tests/test_api tests/test_pipeline tests/test_reports

type-check-aerial:
	python -m mypy src/aerial_housing_detection tests/test_api tests/test_pipeline tests	/test_reports	
	