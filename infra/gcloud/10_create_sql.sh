#!/usr/bin/env bash
set -euo pipefail

: "${PROJECT_ID:?Need PROJECT_ID}"
: "${REGION:=us-central1}"
: "${DB_INSTANCE:=sck-demo-db}"
: "${DB_NAME:=sck}"
: "${DB_USER:=sck}"
: "${DB_PASS:?Need DB_PASS}"

gcloud sql instances create "$DB_INSTANCE" \
  --database-version=POSTGRES_15 \
  --region="$REGION" \
  --cpu=1 --memory=4GB \
  --storage-size=20GB \
  --storage-type=SSD \
  --availability-type=zonal

gcloud sql databases create "$DB_NAME" --instance="$DB_INSTANCE"
gcloud sql users create "$DB_USER" --instance="$DB_INSTANCE" --password="$DB_PASS"

echo "Created Cloud SQL instance: $DB_INSTANCE"
