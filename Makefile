.PHONY: setup init api ui test run-case

setup:
	python -m venv .venv
	. .venv/bin/activate && pip install -r requirements.txt

init:
	python scripts/init_db.py

api:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

ui:
	streamlit run streamlit_app.py

run-case:
	python scripts/run_case.py C0001

test:
	pytest -q
