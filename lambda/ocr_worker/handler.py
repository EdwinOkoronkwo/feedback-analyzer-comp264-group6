import os
import json
import time
import base64
import requests
from scripts.db_config import get_dynamodb_resource

# Initialize Local DynamoDB
dynamodb = get_dynamodb_resource()
# 🎯 ENSURE: Table is 'Metadata' to store intermediate text
table = dynamodb.Table("Metadata")

# --- OCR ENGINE CONFIG ---
OCR_ENGINE = os.getenv('OCR_ENGINE', 'OLLAMA') 

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def lambda_handler(event, context):
    """
    Local OCR Worker: Fixed with Absolute Pathing and Master ID Sync.
    """
    body = event.get('body', {})
    fid = body.get('feedback_id') 
    filename = body.get('filename') 

    # 🎯 PATH FIX: Get the absolute path to the project root
    # This finds the 'uploads' folder regardless of where you start the terminal
    current_dir = os.path.dirname(os.path.abspath(__file__)) # lambda/ocr_worker/
    project_root = os.path.dirname(os.path.dirname(current_dir)) # feedback_analyzer/
    file_path = os.path.join(project_root, "uploads", filename)

    if not os.path.exists(file_path):
        # 🔍 DEBUG: This will show you EXACTLY where it's looking
        print(f"❌ OCR Error: File NOT found at {file_path}")
        return {
            "status": "error", 
            "message": f"File not found at {file_path}",
            "text": "" 
        }

    print(f"🧐 OCR processing ({OCR_ENGINE}) for ID: {fid}")
    base64_image = encode_image(file_path)

    try:
        detected_text = []

        # --- OPTION A: MISTRAL OCR API ---
        if OCR_ENGINE == 'MISTRAL':
            api_key = os.environ.get('MISTRAL_API_KEY')
            response = requests.post(
                "https://api.mistral.ai/v1/ocr",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "mistral-ocr-latest",
                    "document": {
                        "type": "image_url",
                        "image_url": f"data:image/jpeg;base64,{base64_image}"
                    }
                },
                timeout=30
            )
            data = response.json()
            detected_text = [page['markdown'] for page in data.get('pages', [])]

        # --- OPTION B: OLLAMA VISION (Local) ---
        else:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "llama3.2-vision",
                    "prompt": "Transcribe all text in this image exactly. Return only the text.",
                    "images": [base64_image],
                    "stream": False
                },
                timeout=60 
            )
            detected_text = [response.json().get('response', '')]

        full_text = " ".join(detected_text)

        # 🎯 SAVE TO METADATA: Using fid as the key
        table.put_item(Item={
            'feedback_id': fid,          
            'type': 'ocr_result',        
            'text_content': full_text,
            'engine': OCR_ENGINE.lower(),
            'processed_at': str(time.time()),
            'filename': filename
        })
        
        print(f"✅ OCR Success for {fid}")
        
        # 🚀 Return the DICT so the Bridge doesn't crash
        return {
            "status": "success", 
            "feedback_id": fid,
            "text": full_text
        }

    except Exception as e:
        print(f"❌ OCR Error for {fid}: {str(e)}")
        return {
            "status": "error", 
            "feedback_id": fid,
            "message": str(e),
            "text": "" 
        }