.PHONY: install test lint run

install:
	pip install -e ".[dev]"

test:
	pytest -q

lint:
	ruff check .

run:
	streamlit run app.py
