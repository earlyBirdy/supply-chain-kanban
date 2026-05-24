#!/usr/bin/env bash
set -euo pipefail

export PGDATA=${PGDATA:-/var/lib/postgresql/data}
export POSTGRES_USER=${POSTGRES_USER:-demo}
export POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-demo}
export POSTGRES_DB=${POSTGRES_DB:-demo}
export API_PORT=${API_PORT:-7860}

if [ ! -s "$PGDATA/PG_VERSION" ]; then
  mkdir -p "$PGDATA"
  chown -R postgres:postgres "$PGDATA"
  su postgres -c "/usr/lib/postgresql/*/bin/initdb -D '$PGDATA'"
fi

su postgres -c "/usr/lib/postgresql/*/bin/pg_ctl -D '$PGDATA' -o '-c listen_addresses=localhost' -w start"

if ! su postgres -c "psql -tAc \"SELECT 1 FROM pg_roles WHERE rolname='${POSTGRES_USER}'\"" | grep -q 1; then
  su postgres -c "psql -c \"CREATE USER ${POSTGRES_USER} WITH PASSWORD '${POSTGRES_PASSWORD}';\""
fi
if ! su postgres -c "psql -tAc \"SELECT 1 FROM pg_database WHERE datname='${POSTGRES_DB}'\"" | grep -q 1; then
  su postgres -c "createdb -O ${POSTGRES_USER} ${POSTGRES_DB}"
fi

psql "postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:5432/${POSTGRES_DB}" -v ON_ERROR_STOP=1 -f /app/data/seed_sql/00_schema.sql
psql "postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:5432/${POSTGRES_DB}" -v ON_ERROR_STOP=1 -f /app/data/seed_sql/01_seed_demo.sql
psql "postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:5432/${POSTGRES_DB}" -v ON_ERROR_STOP=1 -f /app/data/seed_sql/02_views.sql

exec uvicorn app.api_main:app --host 0.0.0.0 --port "$API_PORT"
