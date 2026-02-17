SHELL := /bin/bash

.PHONY: help demo demo-min demo-ui demo-all seed down reset logs psql status clean test

help:
	@echo "Targets:"
	@echo "  make demo       - start API+agent demo (no UI)"
	@echo "  make demo-min   - start minimal demo (DB+API only)"
	@echo "  make demo-ui    - start demo + Superset UI (profile ui)"
	@echo "  make demo-all   - start full demo + run smoke + print checklist"
	@echo "  make seed       - re-seed demo DB without restarting"
	@echo "  make logs       - tail agent/api logs"
	@echo "  make psql       - open psql in db container"
	@echo "  make status     - show service status + smoke checks"
	@echo "  make down       - stop services (keep volumes)"
	@echo "  make reset      - stop + remove volumes (fresh DB)"
	@echo "  make clean      - remove pycache/pyc/bak/test caches"
	@echo "  make test       - run unit tests (local python)"

clean:
	@./scripts/clean.sh

demo:
	@if [[ ! -f .env ]]; then echo "No .env found. Create one: cp .env.example .env"; fi
	docker compose down -v || true
	docker compose --profile agent up -d --build
	@./scripts/demo_smoke.sh agent
	@echo "API docs: http://localhost:8000/docs"
	@echo "Tail logs: make logs"

demo-min:
	@if [[ ! -f .env ]]; then echo "No .env found. Create one: cp .env.example .env"; fi
	docker compose down -v || true
	docker compose up -d --build
	@./scripts/demo_smoke.sh
	@echo "API docs: http://localhost:8000/docs"

demo-ui:
	@if [[ ! -f .env ]]; then echo "No .env found. Create one: cp .env.example .env"; fi
	docker compose down -v || true
	docker compose --profile ui --profile agent up -d --build
	@./scripts/demo_smoke.sh ui
	@echo "API docs: http://localhost:8000/docs"
	@echo "Superset: http://localhost:8088 (login SUPERSET_ADMIN_USER/SUPERSET_ADMIN_PASS from .env)"

demo-all:
	@$(MAKE) demo-ui
	@./scripts/demo_checklist.sh

seed:
	@POSTGRES_USER=$${POSTGRES_USER:-demo}; POSTGRES_DB=$${POSTGRES_DB:-demo}; \
	docker compose exec -T db psql -U $$POSTGRES_USER -d $$POSTGRES_DB -f /seed/01_seed_demo.sql
	@echo "Re-seeded demo data."

logs:
	docker compose --profile agent logs -f agent api

psql:
	@POSTGRES_USER=$${POSTGRES_USER:-demo}; POSTGRES_DB=$${POSTGRES_DB:-demo}; \
	docker compose exec -T db psql -U $$POSTGRES_USER -d $$POSTGRES_DB

down:
	docker compose down || true

reset:
	docker compose down -v || true
	@echo "Removed volumes. Next: make demo, make demo-ui, or make demo-all"

status:
	@echo "== docker compose ps =="
	docker compose ps
	@echo ""
	@./scripts/demo_smoke.sh
	@echo ""
	@echo "(To include Superset UI checks: ./scripts/demo_smoke.sh ui)"
	@./scripts/demo_checklist.sh

test:
	@PYTHONPATH=agent_runtime pytest -q
