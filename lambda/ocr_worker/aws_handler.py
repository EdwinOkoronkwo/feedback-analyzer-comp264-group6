import boto3
import json
import time

textract = boto3.client('textract', region_name='us-east-1')
s3 = boto3.client('s3', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
lambda_client = boto3.client('lambda', region_name='us-east-1')

def lambda_handler(event, context):
    # 🎯 FIX: Priority ID Check
    # Use the passed feedback_id first, otherwise fallback to filename
    record = event['Records'][0]
    bucket = record['s3']['bucket']['name']
    full_key = record['s3']['object']['key'] 
    
    fid = event.get('feedback_id')
    if not fid:
        filename = full_key.split('/')[-1]
        fid = filename.rsplit('.', 1)[0]

    try:
        is_text_file = full_key.lower().endswith('.txt')
        is_image = any(full_key.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg'])

        print(f"📸 OCR Worker: {fid} | Image: {is_image}")
        full_text = ""

        if is_text_file:
            response = s3.get_object(Bucket=bucket, Key=full_key)
            full_text = response['Body'].read().decode('utf-8')
        elif is_image:
            response = textract.detect_document_text(
                Document={'S3Object': {'Bucket': bucket, 'Name': full_key}}
            )
            detected_text = [item['Text'] for item in response['Blocks'] if item['BlockType'] == 'LINE']
            full_text = " ".join(detected_text)

        if not full_text.strip():
            full_text = "No readable text found."

        # Update DB
        table = dynamodb.Table('Analysis_Summaries')
        table.update_item(
            Key={'feedback_id': fid},
            UpdateExpression="SET #s = :stat, raw_text = :txt, #m = :msg",
            ExpressionAttributeNames={'#s': 'status', '#m': 'master'},
            ExpressionAttributeValues={
                ':stat': 'OCR_COMPLETED',
                ':txt': full_text,
                ':msg': "OCR Complete. Sending to Analysis."
            }
        )
        
        # Invoke Analysis
        lambda_client.invoke(
            FunctionName='analysis_worker',
            InvocationType='Event',
            Payload=json.dumps({"feedback_id": fid, "text": full_text}).encode('utf-8')
        )
        
        return {"status": "success", "feedback_id": fid}

    except Exception as e:
        print(f"❌ OCR Error for {fid}: {str(e)}")
        return {"status": "error", "message": str(e)}