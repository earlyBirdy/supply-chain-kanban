#!/usr/bin/env bash
set -euo pipefail

: "${PROJECT_ID:?Set PROJECT_ID}"
REGION="${REGION:-us-central1}"
AR_REPO="${AR_REPO:-supply-chain-kanban}"

gcloud builds submit --tag "$REGION-docker.pkg.dev/$PROJECT_ID/$AR_REPO/sck-api:latest" apps/api
gcloud builds submit --tag "$REGION-docker.pkg.dev/$PROJECT_ID/$AR_REPO/sck-web:latest" apps/web

printf 'Built API and Web images. Configure runtime env, DB, contracts, governance policy, and secrets before deploy.
'
