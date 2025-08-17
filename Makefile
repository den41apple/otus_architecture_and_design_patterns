.PHONY: install test coverage

install_dependencies:
	python -m pip install --upgrade pip && \
	python -m pip install uv==0.8.11 && \
	uv sync --active --dev --all-extras

uv_sync:
	uv sync --active --dev --all-extras

linters_check:
	ruff format --check .
	ruff check .

linters:
	ruff format .
	ruff check . --fix

run_tests:
	uv run pytest -vvx

coverage:
	PYTHONPATH=$(pwd) pytest --cov=homeworks --cov-report=term-missing --cov-report=html tests
