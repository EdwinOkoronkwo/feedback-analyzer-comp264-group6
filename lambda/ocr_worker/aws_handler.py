import boto3
import json
import os

# Initialize Clients
textract = boto3.client('textract', region_name='us-east-1')
s3 = boto3.client('s3', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
lambda_client = boto3.client('lambda', region_name='us-east-1')

def lambda_handler(event, context):
    fid = 'unknown'
    try:
        # 1. Parse S3 Event
        record = event['Records'][0]
        bucket = record['s3']['bucket']['name']
        full_key = record['s3']['object']['key'] 
        
        # Extract ID (e.g., "uploads/admin_123.jpg" -> "admin_123")
        filename = full_key.split('/')[-1]
        fid = filename.rsplit('.', 1)[0]
        is_text_file = full_key.lower().endswith('.txt')

        print(f"📸 OCR Worker: Processing {fid} (Is Text: {is_text_file})")

        full_text = ""

        # 2. 🎯 THE BYPASS: If it's a .txt file, don't call Textract
        if is_text_file:
            print(f"📄 Reading raw text from S3 for {fid}")
            response = s3.get_object(Bucket=bucket, Key=full_key)
            full_text = response['Body'].read().decode('utf-8')
        else:
            # AWS Textract: Extract Text from Images
            print(f"🔍 Running Textract OCR for {fid}")
            response = textract.detect_document_text(
                Document={'S3Object': {'Bucket': bucket, 'Name': full_key}}
            )
            detected_text = [item['Text'] for item in response['Blocks'] if item['BlockType'] == 'LINE']
            full_text = " ".join(detected_text)

        if not full_text.strip():
            full_text = "No readable text found."

        # 3. DynamoDB: Save Raw Text
        dynamodb.Table('Analysis_OCR').put_item(Item={
            'feedback_id': fid,          
            'text': full_text,
            'status': 'OCR_COMPLETED',
            'timestamp': str(os.times()[4])
        })
        
        # 4. RELAY: Trigger Analysis Worker (Comprehend)
        # 🚀 This ensures the "Baton Pass" continues for text inputs
        lambda_client.invoke(
            FunctionName='analysis_worker',
            InvocationType='Event',
            Payload=json.dumps({"feedback_id": fid, "text": full_text}).encode('utf-8')
        )
        
        return {"status": "success", "feedback_id": fid}

    except Exception as e:
        print(f"❌ OCR Error for {fid}: {str(e)}")
        return {"status": "error", "message": str(e)}