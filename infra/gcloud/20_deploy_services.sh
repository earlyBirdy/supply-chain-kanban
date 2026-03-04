#!/usr/bin/env bash
set -euo pipefail

: "${PROJECT_ID:?Need PROJECT_ID}"
: "${REGION:=us-central1}"
: "${DB_INSTANCE:=sck-demo-db}"
: "${DB_NAME:=sck}"
: "${DB_USER:=sck}"
: "${DB_PASS:?Need DB_PASS}"

# Create Artifact Registry
AR_REPO="sck"
gcloud artifacts repositories create "$AR_REPO" --repository-format=docker --location="$REGION" || true

# Build + deploy API
gcloud builds submit --tag "$REGION-docker.pkg.dev/$PROJECT_ID/$AR_REPO/sck-api:latest" .
gcloud run deploy sck-api \
  --image "$REGION-docker.pkg.dev/$PROJECT_ID/$AR_REPO/sck-api:latest" \
  --allow-unauthenticated \
  --set-env-vars "DATABASE_URL=postgresql://$DB_USER:$DB_PASS@/cloudsql/$PROJECT_ID:$REGION:$DB_INSTANCE/$DB_NAME" \
  --add-cloudsql-instances "$PROJECT_ID:$REGION:$DB_INSTANCE" \
  --port 8000

# Deploy orchestrator (optional)
gcloud builds submit --tag "$REGION-docker.pkg.dev/$PROJECT_ID/$AR_REPO/sck-orchestrator:latest" live_orchestrator
gcloud run deploy sck-orchestrator \
  --image "$REGION-docker.pkg.dev/$PROJECT_ID/$AR_REPO/sck-orchestrator:latest" \
  --allow-unauthenticated \
  --set-env-vars "API_BASE=https://sck-api-REPLACE.a.run.app,ORCHESTRATOR_MODE=scaffold" \
  --port 8081

# Deploy web demo (static)
gcloud builds submit --tag "$REGION-docker.pkg.dev/$PROJECT_ID/$AR_REPO/sck-web:latest" web_demo
gcloud run deploy sck-web \
  --image "$REGION-docker.pkg.dev/$PROJECT_ID/$AR_REPO/sck-web:latest" \
  --allow-unauthenticated \
  --port 8080

echo "Deployed. Update the API_BASE env on sck-orchestrator to point at your sck-api URL."
