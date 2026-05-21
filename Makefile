SHELL := /bin/bash

.PHONY: help demo demo-min demo-web demo-agent demo-signals seed down reset logs psql status clean test test-fast debug-ui

help:
	@echo "Targets:"
	@echo "  make demo          - start DB + API + Kanban web board (default demo)"
	@echo "  make demo-min      - start DB + API"
	@echo "  make demo-web      - start DB + API + Kanban web board"
	@echo "  make demo-agent    - start DB + API + background agent"
	@echo "  make demo-signals  - start optional market signal monitor"
	@echo "  make seed          - re-seed demo DB without restarting"
	@echo "  make logs          - tail API/agent logs"
	@echo "  make psql          - open psql in db container"
	@echo "  make status        - show service status + smoke checks"
	@echo "  make down          - stop services"
	@echo "  make reset         - stop + remove volumes"
	@echo "  make clean         - remove generated caches"
	@echo "  make test          - run Python compile checks + pytest"
	@echo "  make test-fast     - run pytest only"
	@echo "  make debug-ui      - start Streamlit AI-agent debug cockpit"

clean:
	@bash ./scripts/clean.sh

# Default browser demo alias.
demo:
	@$(MAKE) demo-web

demo-min:
	@if [[ ! -f .env ]]; then echo "No .env found. Create one: cp .env.example .env"; fi
	docker compose down -v || true
	docker compose up -d --build
	@bash ./scripts/demo_smoke.sh
	@echo "API docs: http://localhost:8000/docs"

demo-web:
	@if [[ ! -f .env ]]; then echo "No .env found. Create one: cp .env.example .env"; fi
	docker compose down -v || true
	docker compose --profile web up -d --build
	@bash ./scripts/demo_smoke.sh web
	@echo "API docs: http://localhost:8000/docs"
	@echo "Kanban board: http://localhost:8080"

demo-agent:
	@if [[ ! -f .env ]]; then echo "No .env found. Create one: cp .env.example .env"; fi
	docker compose down -v || true
	docker compose --profile agent --profile web up -d --build
	@bash ./scripts/demo_smoke.sh web
	@echo "API docs: http://localhost:8000/docs"
	@echo "Kanban board: http://localhost:8080"

demo-signals:
	@if [[ ! -f .env ]]; then echo "No .env found. Create one: cp .env.example .env"; fi
	docker compose --profile signals up -d --build
	@echo "Signal monitor started. Tail logs with: docker compose logs -f news_monitor"

seed:
	@POSTGRES_USER=$${POSTGRES_USER:-demo}; POSTGRES_DB=$${POSTGRES_DB:-demo}; 	docker compose exec -T db psql -U $$POSTGRES_USER -d $$POSTGRES_DB -f /seed/01_seed_demo.sql
	@echo "Re-seeded demo data."

logs:
	docker compose logs -f api agent news_monitor

psql:
	@POSTGRES_USER=$${POSTGRES_USER:-demo}; POSTGRES_DB=$${POSTGRES_DB:-demo}; 	docker compose exec -T db psql -U $$POSTGRES_USER -d $$POSTGRES_DB

down:
	docker compose down || true

reset:
	docker compose down -v || true
	@echo "Removed volumes. Next: make demo-min or make demo-web"

status:
	@echo "== docker compose ps =="
	docker compose ps
	@echo ""
	@bash ./scripts/demo_smoke.sh
	@bash ./scripts/demo_checklist.sh

test:
	@python3 scripts/run_checks.py

test-fast:
	@PYTHONPATH=apps/api pytest -q

debug-ui:
	@python3 -m streamlit run apps/debug_ui/streamlit_app.py --server.port 8501
