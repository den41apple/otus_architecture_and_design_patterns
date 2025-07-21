.PHONY: install test coverage

install_dependencies:
	python -m pip install --upgrade pip && \
	python -m pip install poetry==2.1.3 && \
	poetry config virtualenvs.create false --local && \
	python -m poetry install --no-interaction

run_tests:
	poetry run pytest -vvx

coverage:
	PYTHONPATH=$(pwd) pytest --cov=homeworks --cov-report=term-missing --cov-report=html tests
