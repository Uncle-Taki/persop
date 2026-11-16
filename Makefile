.PHONY: check up down demo logs
check:
	cd persob && go test ./... && go vet ./... && go build ./cmd/perso ./cmd/llm-mock
	cd persof && npm ci && npm run check:api && npm run typecheck && npm run build
	python3 scripts/check-contract.py
up:
	docker compose up -d --build
down:
	docker compose down
demo:
	docker compose -p perso-demo -f compose.yaml -f compose.demo.yaml up -d --build
logs:
	docker compose logs --tail=100 -f
# Volume deletion intentionally requires a separate, explicit command in the runbook.
