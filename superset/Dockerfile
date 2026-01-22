FROM apache/superset:latest

USER root
# Ensure pip exists for the venv, then install psycopg2-binary in the SAME venv Superset uses.
RUN /app/.venv/bin/python -m ensurepip --upgrade || true
RUN /app/.venv/bin/python -m pip install --no-cache-dir psycopg2-binary

USER superset
