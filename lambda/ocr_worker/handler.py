import os
import json
import time
import pytesseract
from PIL import Image
import requests
from scripts.db_config import get_dynamodb_resource

# Initialize Local DynamoDB
dynamodb = get_dynamodb_resource()
table = dynamodb.Table('Summaries') 

def lambda_handler(event, context=None):
    """
    🏛️ TESSERACT WORKER: 
    Extracts text locally and relays to Mistral AI.
    """
    fid = event.get('feedback_id')
    file_path = event.get('file_path')
    
    if not file_path or not os.path.exists(file_path):
        print(f"❌ [KAG] Path Error: {file_path}")
        return {"status": "error", "message": "File not found"}

    print(f"🧐 [KAG] Processing TESSERACT OCR for ID: {fid}")
    
    try:
        # 1. Local Tesseract OCR
        # We open the image and convert it to string
        raw_text = pytesseract.image_to_string(Image.open(file_path)).strip()

        # Fallback if OCR is totally blank
        if not raw_text:
            raw_text = f"OCR skipped: No text detected in image {fid}."

        # 2. 💾 SEED THE DATABASE
        table.put_item(Item={
            'feedback_id': fid,
            'status': 'OCR_COMPLETE',
            'text': raw_text,
            'processed_at': str(time.time()),
            'engine': 'tesseract_local'
        })

        # 3. 🚀 RELAY TO SUMMARY WORKER
        print(f"🔗 [KAG] Relaying {fid} to AI Worker...")
        try:
            requests.post(
                "http://localhost:5001/process-summary", 
                json={"body": {"feedback_id": fid, "text": raw_text}},
                timeout=0.1 
            )
        except requests.exceptions.ReadTimeout:
            pass 

        return {"status": "success", "id": fid}

    except Exception as e:
        print(f"🔥 [KAG-ERROR]: {str(e)}")
        return {"status": "error", "msg": str(e)}