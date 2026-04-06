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
    Local OCR extraction and relay to Mistral AI.
    """
    fid = event.get('feedback_id')
    file_path = event.get('file_path')
    folder = event.get('folder', 'Email')
    
    if not file_path or not os.path.exists(file_path):
        print(f"❌ [KAG] Path Error: {file_path}")
        return {"status": "error", "message": f"Invalid path: {file_path}"}

    print(f"🧐 [KAG] Processing TESSERACT OCR for ID: {fid}")
    
    try:
        # 1. Local Tesseract OCR
        # Opening the image and extracting text string
        text = pytesseract.image_to_string(Image.open(file_path)).strip()

        # 🎯 SAFETY: If Tesseract returns nothing, we send a placeholder 
        # so the Summary Worker (Mistral) doesn't "Skip" it.
        if not text:
            print(f"⚠️ [KAG] Tesseract found no text for {fid}. Sending fallback.")
            text = f"Document ID: {fid} - OCR could not extract text from this image."

        # 2. 💾 SEED THE DATABASE
        table.put_item(Item={
            'feedback_id': fid,
            'status': 'OCR_COMPLETE',
            'text': text,
            'category': folder,
            'processed_at': str(time.time()),
            'engine': 'tesseract_local'
        })

        # 3. 🚀 RELAY TO SUMMARY WORKER (Mistral)
        # This keeps the automation moving to the AI step
        print(f"🔗 [KAG] Relaying {fid} to AI Worker...")
        try:
            requests.post(
                "http://localhost:5001/process-summary", 
                json={"body": {"feedback_id": fid, "text": text}},
                timeout=0.1 
            )
        except requests.exceptions.ReadTimeout:
            pass 

        return {"status": "success", "id": fid}

    except Exception as e:
        print(f"🔥 [KAG-ERROR]: {str(e)}")
        return {"status": "error", "msg": str(e)}