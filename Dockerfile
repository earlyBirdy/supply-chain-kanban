# Hugging Face Spaces single-container demo for Supply Chain AI Agent.
# Set the Space SDK to Docker and let this container serve both API and UI on port 7860.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    SUPPLY_CHAIN_SERVE_WEB=1 \
    SUPPLY_CHAIN_WEB_STATIC_DIR=/app/web \
    API_PORT=7860 \
    POSTGRES_USER=demo \
    POSTGRES_PASSWORD=demo \
    POSTGRES_DB=demo \
    AGENT_DB_URL=postgresql+psycopg2://demo:demo@localhost:5432/demo \
    ERP_CONNECTOR=mock \
    GOV_POLICY_PATH=/app/operations/governance/policy.yaml \
    DEMO_EXPERIENCE_PACK_PATH=/app/contracts/demo_experience_pack.yaml \
    DEMO_STORY_PACK_PATH=/app/contracts/demo_story_pack.yaml \
    LIFECYCLE_MODEL_PATH=/app/contracts/lifecycle_model.yaml \
    ONTOLOGY_PATH=/app/contracts/supply_chain_ontology.yaml

RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql postgresql-contrib \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY apps/api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY apps/api/app /app/app
COPY apps/web/public /app/web
COPY contracts /app/contracts
COPY operations/governance /app/operations/governance
COPY data/seed_sql /app/data/seed_sql
COPY scripts/hf_start.sh /app/scripts/hf_start.sh
RUN chmod +x /app/scripts/hf_start.sh

EXPOSE 7860
CMD ["/app/scripts/hf_start.sh"]
