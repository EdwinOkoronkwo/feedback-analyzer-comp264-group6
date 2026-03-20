import time
import os
import json
import base64
import requests
import logging
from scripts.db_config import get_dynamodb_resource

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Local DynamoDB
dynamodb = get_dynamodb_resource()
# 🎯 FIX 1: Align with the 'Metadata' table in your local setup
table = dynamodb.Table('Metadata')

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def lambda_handler(event, context):
    """
    Local Label Worker: Uses Ollama Vision and saves to the Metadata table.
    """
    logger.info("🔔 Local Label Worker Triggered")

    try:
        # 1. Parse Input
        body = event.get('body', {})
        filename = body.get('filename')
        
        # 🎯 FIX 2: Stop the "Rubbish" ID generation.
        # Use the feedback_id passed by the bridge. No splitting!
        feedback_id = body.get('feedback_id') or filename
        
        file_path = os.path.join("uploads", filename)

        if not os.path.exists(file_path):
            logger.error(f"❌ File not found: {file_path}")
            return {"status": "error", "message": f"File {filename} not found", "labels": []}

        # 2. Process with Ollama Vision
        logger.info(f"📸 Identifying objects in: {filename} for ID: {feedback_id}")
        base64_image = encode_image(file_path)

        prompt = "Identify the main objects and themes. Return only a comma-separated list of labels."

        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3.2-vision",
                "prompt": prompt,
                "images": [base64_image],
                "stream": False
            },
            timeout=45 # Vision can be slow
        )
        response.raise_for_status()
        
        raw_labels = response.json().get('response', '')
        labels = [l.strip() for l in raw_labels.split(',') if l.strip()]
        
        logger.info(f"🏷️ Labels found: {labels}")

        # 3. Save to Local DynamoDB (Metadata Table)
        # 🎯 FIX 3: Use 'type' as a sort-key equivalent for the Metadata table
        table.put_item(Item={
            'feedback_id': feedback_id,
            'type': 'image_labels',
            'labels': labels,
            'engine': 'ollama-vision-local',
            'processed_at': str(time.time()),
            'filename': filename
        })
        
        logger.info(f"✅ Successfully wrote labels to Metadata for: {feedback_id}")
        return {"status": "success", "labels": labels, "feedback_id": feedback_id}

    except Exception as e:
        logger.error(f"❌ Error in Label Worker: {str(e)}")
        return {"status": "error", "message": str(e), "labels": []}