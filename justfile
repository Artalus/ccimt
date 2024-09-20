all: format lint test


venv:
	uv venv
	uv pip install -e .[dev]



test:
	pytest --cov --cov-report xml

lint: ruff mypy

ruff:
	ruff check --fix .

format:
	ruff format .

mypy:
	mypy .
