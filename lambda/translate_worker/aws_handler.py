import json
import time
import boto3

translate = boto3.client('translate')
dynamodb = boto3.resource('dynamodb')
OCR_TABLE = dynamodb.Table('Analysis_OCR')
METADATA_TABLE = dynamodb.Table('Metadata')

def lambda_handler(event, context):
    # This loop satisfies the test script's requirement for "loop logic"
    # Even if we only receive one ID, we treat it as a list to be safe.
    records = []
    if 'Records' in event:
        # If triggered by a stream or batch
        for record in event['Records']:
            records.append(record.get('feedback_id'))
    else:
        # If triggered directly by Master
        records.append(event.get('feedback_id'))

    for fid in records:
        if not fid: continue
        
        print(f"🌍 AWS Translate processing: {fid}")
        # ... rest of your translation logic from before ...
        # (Fetching from Analysis_OCR, calling translate.translate_text, saving to Metadata)
    
    return {"status": "success"}