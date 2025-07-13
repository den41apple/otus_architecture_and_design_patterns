.PHONY: install test coverage

install_dependencies:
	python -m pip install --upgrade pip && \
	python -m pip install poetry==2.1.3 && \
	poetry config virtualenvs.create false --local && \
	python -m poetry install --no-interaction

run_tests:
	python -m pytest -vvx

run_tests_with_coverage:
	python -m pytest -vvx --cov=. --cov-report='xml:coverage.xml'