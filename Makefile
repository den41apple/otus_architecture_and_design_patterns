.PHONY: install test coverage

install_dependencies:
	python -m pip install --upgrade pip && \
	python -m pip install -r requirements.txt && \
	poetry config virtualenvs.create false --local && \
	python -m poetry install

run_tests:
	python -m pytest -vvx

run_tests_with_coverage:
	python -m pytest -vvx --cov=. --cov-report='xml:coverage.xml'