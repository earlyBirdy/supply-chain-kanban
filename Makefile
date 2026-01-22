demo:
	docker compose down -v || true
	docker compose up -d --build
	sleep 2
	docker compose exec -T db psql -U demo -d demo -c "CREATE EXTENSION IF NOT EXISTS pgcrypto;"
	docker compose exec -T db psql -U demo -d demo -f /seed/00_schema.sql
	docker compose exec -T db psql -U demo -d demo -f /seed/01_seed_demo.sql
	docker compose exec -T db psql -U demo -d demo -f /seed/02_views.sql
	@echo "Demo running. Tail agent logs: make logs"
	@echo "Open psql: make psql"

logs:
	docker compose logs -f agent

psql:
	docker compose exec -T db psql -U demo -d demo


demo-ui:
	docker compose down -v || true
	docker compose up -d --build
	sleep 2
	docker compose exec -T db psql -U demo -d demo -c "CREATE EXTENSION IF NOT EXISTS pgcrypto;"
	docker compose exec -T db psql -U demo -d demo -f /seed/00_schema.sql
	docker compose exec -T db psql -U demo -d demo -f /seed/01_seed_demo.sql
	docker compose exec -T db psql -U demo -d demo -f /seed/02_views.sql
	docker compose exec -T superset superset db upgrade || true
	docker compose exec -T superset superset init || true
	@echo "UI demo: Superset at http://localhost:8088 (login admin/admin)"
	@echo "Agent logs: make logs"


status:
	@echo "== docker compose ps =="
	docker compose ps
	@echo ""
	@echo "== superset health =="
	@docker compose exec -T superset curl -sf http://localhost:8088/health && echo "OK" || (echo "Superset health check FAILED"; exit 1)
	@echo ""
	@echo "== db ping =="
	@docker compose exec -T db psql -U demo -d demo -c "select 1;" >/dev/null && echo "DB OK" || (echo "DB check FAILED"; exit 1)
	@echo ""
	@echo "== agent logs (last 20 lines) =="
	@docker compose logs --tail=20 agent


reset-ui:
	docker compose down -v || true
	@echo "Removed volumes. Next: make demo-ui"
