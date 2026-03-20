🛡️ AI Sentinel: Feedback Analyzer

Hybrid Multi-Modal Analysis Pipeline (VMware & AWS)

This project is a decoupled, N-Tier feedback analysis engine. It supports Local Development (VMware) and Cloud Production (AWS).
🏗️ Architecture: The Two Worlds

The system uses a shared UI component library but swaps the "Engine" based on which app you launch.
1. Local Stack (VMware)

    Purpose: Rapid development, zero cost, private data.

    OCR & Vision: Tesseract and Ollama (Local models).

    Brain (LLM): Mistral API (Medium/Small).

    Speech: gTTS (Saves to static/audio/).

    Database: DynamoDB Local (Running on localhost:8000).

    Storage: Local Filesystem.

2. Cloud Stack (AWS)

    Purpose: High availability, scale, and managed services.

    OCR & Vision: AWS Textract and Rekognition.

    Brain (LLM): Mistral API (Large/Medium).

    Speech: AWS Polly (Saves to S3 URL).

    Database: AWS DynamoDB (Managed tables).

    Storage: AWS S3 Buckets.

🚀 Quick Start: Local (VMware)

    Start Database: Ensure Docker is running and start DynamoDB Local:
    docker run -p 8000:8000 amazon/dynamodb-local

    Start Backend Bridge: Run the Flask app to handle local worker requests:
    python local_bridge/app.py

    Launch UI:
    streamlit run web/app_local.py

☁️ Quick Start: Cloud (AWS)

    Deploy Workers: Use Chalice to push the Lambda functions:
    cd workers/ && chalice deploy

    Check Credentials: Ensure your ~/.aws/credentials has the correct profile active.

    Launch UI:
    streamlit run web/app_aws.py

📁 Key File Structure

    web/app_local.py: Entry point for the VMware stack.

    web/app_aws.py: Entry point for the AWS stack.

    chalicelib/local/: Logic for local orchestration and persistence.

    chalicelib/aws/: Logic for AWS service providers and cloud handlers.

    web/components/: Agnostic UI elements that work with either stack.

🛠️ Troubleshooting AWS Reconnection

    Permissions: If you see "Access Denied," ensure your IAM User has AmazonS3FullAccess and AmazonDynamoDBFullAccess.

    Tables: The Cloud app expects tables named Metadata and Summaries. Ensure these exist in your AWS Console.

    S3: Ensure the bucket name in your .env or AWS Environment Variables matches your real S3 bucket.