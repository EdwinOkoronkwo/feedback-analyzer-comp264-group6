import json
import os
import boto3
import time

# Initialize AWS Clients
s3 = boto3.client('s3')
region = os.getenv('AWS_REGION', 'us-east-1')
dynamodb = boto3.resource('dynamodb', region_name=region)
lambda_client = boto3.client('lambda', region_name=region)

def lambda_handler(event, context):
    """
    NIST Relayer: Standardizes NIST batch samples and triggers OCR Worker.
    Triggered by: AWSPipelineBridge (Local VMware)
    """
    fid = event.get('feedback_id', f"nist_auth_{int(time.time())}")
    
    try:
        # 1. Extract Data from Bridge Payload
        label = event.get('label', 'Unknown')
        raw_text = f"NIST Authentic Data: This handwritten character represents the class {label}."
        image_url = event.get('image_url', '') # Format: s3://bucket-name/key/path/file.png
        bucket = event.get('bucket', 'comp264-edwin-1772030214')

        # Extract the S3 Key from the URL for the OCR Worker
        # Removes "s3://bucket-name/" to get just the key
        s3_key = image_url.replace(f"s3://{bucket}/", "")

        print(f"🏛️ NIST Relayer: Processing Authentic Sample {fid} (Label: {label})")

        # 2. 📝 UI FOOTPRINT: Initialize the Analysis_Summaries table
        table = dynamodb.Table('Analysis_Summaries')
        table.put_item(Item={
            'feedback_id': fid,
            'status': 'PROCESSING_BATCH',
            'dataset_type': 'NIST_AUTHENTIC',
            'raw_text': raw_text,
            'image_path': image_url,
            'timestamp': str(int(time.time())),
            'master': "NIST Relayer: Handing off to OCR Worker for Textract analysis."
        })

        # 3. 🎯 THE BATON PASS: Mimic S3 Event for ocr_worker
        # This allows the ocr_worker to use its record['s3']['object']['key'] logic
        ocr_payload = {
            "Records": [{
                "s3": {
                    "bucket": {"name": bucket},
                    "object": {"key": s3_key}
                }
            }]
        }

        print(f"🚀 Passing Baton to ocr_worker for {fid}...")
        
        lambda_client.invoke(
            FunctionName='ocr_worker',
            InvocationType='Event',
            Payload=json.dumps(ocr_payload).encode('utf-8')
        )

        return {
            "status": "success",
            "feedback_id": fid,
            "next_step": "ocr_worker_triggered"
        }

    except Exception as e:
        print(f"❌ NIST Relayer Error for {fid}: {str(e)}")
        try:
            dynamodb.Table('Analysis_Summaries').update_item(
                Key={'feedback_id': fid},
                UpdateExpression="set #s = :err",
                ExpressionAttributeNames={'#s': 'status'},
                ExpressionAttributeValues={':err': 'RELAY_FAILED'}
            )
        except:
            pass
            
        return {"status": "error", "message": str(e)}