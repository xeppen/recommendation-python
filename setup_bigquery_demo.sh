#!/bin/bash

# Setup script för we-select-data-dev projektet
PROJECT_ID="we-select-data-dev-422614"
DATASET_ID="recruitment_demo"
SERVICE_ACCOUNT_NAME="recruitment-app-demo"

echo "🚀 BigQuery Demo Setup för we-select-data-dev"
echo "=============================================="

# Sätt projekt
echo "📍 Sätter aktivt projekt..."
gcloud config set project $PROJECT_ID

# Aktivera BigQuery API
echo "🔧 Aktiverar BigQuery API..."
gcloud services enable bigquery.googleapis.com

# Skapa service account
echo "👤 Skapar service account..."
gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
    --display-name="Recruitment App Demo" \
    --project=$PROJECT_ID 2>/dev/null || echo "Service account finns redan"

# Ge BigQuery rättigheter
echo "🔐 Ger BigQuery rättigheter..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/bigquery.dataEditor" \
    --quiet

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/bigquery.jobUser" \
    --quiet

# Skapa service account key
echo "🔑 Skapar service account nyckel..."
gcloud iam service-accounts keys create service-account-demo.json \
    --iam-account="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --project=$PROJECT_ID

echo ""
echo "✅ Setup klar!"
echo ""
echo "Nästa steg:"
echo "1. export GOOGLE_APPLICATION_CREDENTIALS='service-account-demo.json'"
echo "2. python3 upload_to_bigquery.py"
echo ""
echo "Dataset: $DATASET_ID"
echo "Project: $PROJECT_ID"
