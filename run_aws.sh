#!/bin/bash

# --- 1. Load Environment Variables ---
# Ensure your MISTRAL_API_KEY and AWS credentials are in your .env
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
    echo "✅ Environment variables loaded from .env"
else
    echo "⚠️  No .env file found. Ensure AWS_ACCESS_KEY_ID is set in your shell."
fi

# --- 2. Infrastructure & Worker Deployment ---
echo "🏗️  Starting AWS Infrastructure Deployment..."
# This calls the script you shared earlier to build S3, Dynamo, and Lambdas
python3 scripts/deploy_all.py

if [ $? -ne 0 ]; then
    echo "❌ Deployment failed. Aborting UI launch."
    exit 1
fi

echo "✨ AWS Infrastructure is Synchronized."

# --- 3. Launch Streamlit in AWS Mode ---
echo "🖥️  Launching Streamlit UI (Production Mode)..."
# We pass an environment flag so your Factory knows to use AWS providers
export APP_MODE="PROD" 
streamlit run web/app.py