install:
	pip install -e ".[dev,api]"

test:
	pytest -q

serve:
	uvicorn api.main:app --reload --port 8080

ui-dev:
	cd ui && npm run dev

ui-build:
	cd ui && npm run build
