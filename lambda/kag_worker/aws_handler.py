import json
import boto3
import time

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

def lambda_handler(event, context):
    fid = event.get('feedback_id', f"kag_batch_{int(time.time())}")
    bucket = event.get('bucket', 'comp264-edwin-1772030214')
    image_url = event.get('image_url', '')
    folder = event.get('folder', 'Unknown')
    
    # Extract the clean S3 key from the URL
    s3_key = image_url.replace(f"s3://{bucket}/", "")

    try:
        print(f"🏛️ KAG Worker: Processing {fid}")

        # 1. Seed DynamoDB
        table = dynamodb.Table('Analysis_Summaries')
        table.put_item(Item={
            'feedback_id': fid,
            'status': 'PROCESSING_KAG',
            'dataset_type': f'KAG_{folder.upper()}',
            'image_path': image_url,
            'timestamp': str(time.time()),
            'master': f"KAG Worker initialized {folder} document."
        })

        # 2. Determine file type
        file_ext = s3_key.split('.')[-1].lower()

        # 🎯 RELAY LOGIC: Standardize the payload for the ocr_worker
        relay_payload = {
            "feedback_id": fid,
            "Records": [{
                "s3": {
                    "bucket": {"name": bucket},
                    "object": {"key": s3_key}
                }
            }]
        }

        if file_ext in ['jpg', 'jpeg', 'png', 'txt']:
            print(f"🚀 Relaying {fid} to OCR Worker...")
            lambda_client.invoke(
                FunctionName='ocr_worker',
                InvocationType='Event',
                Payload=json.dumps(relay_payload).encode('utf-8')
            )
        
        return {"status": "success", "id": fid}

    except Exception as e:
        print(f"🛑 [FATAL ERROR] {str(e)}")
        return {"status": "error", "message": str(e)}