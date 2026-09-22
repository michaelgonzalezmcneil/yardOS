.PHONY: dev test demo down

dev:
	docker compose up --build

test:
	docker compose run --rm api pytest -q
	docker compose run --rm web npm test

demo:
	docker compose up --build -d db api web
	curl -s -X POST http://localhost:8000/demo/load
	@echo "YardOS demo: http://localhost:3000/sites/houston-yard-1"

down:
	docker compose down
