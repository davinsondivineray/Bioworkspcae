.PHONY: install dev migrate test lint seed cdk-synth

install:
	python3 -m pip install -r requirements-dev.txt

dev:
	uvicorn app.main:app --reload

migrate:
	alembic upgrade head

test:
	pytest -q

lint:
	ruff check app tests infra worker.py seed.py

seed:
	python3 seed.py

cdk-synth:
	cdk synth
