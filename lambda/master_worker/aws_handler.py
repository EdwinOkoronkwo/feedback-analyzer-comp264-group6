import boto3
import json
import os
import time

# Initialize Clients
lambda_client = boto3.client('lambda')
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

def lambda_handler(event, context):
    fid = 'unknown'
    try:
        # 1. Extract File Info
        record = event['Records'][0]
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        
        fid = key.split('/')[-1].rsplit('.', 1)[0]
        file_ext = key.split('.')[-1].lower()
        # ⏱️ Synthetic Lag: Let the user see the Master icon turn green
        time.sleep(2)

        print(f"🎮 Master Orchestrator: Processing {fid} (Type: {file_ext})")

        # 2. 📝 LEAVE A FOOTPRINT: Update UI that Master has the baton
        # This turns the 🎮 emoji green in your Streamlit UI
        table = dynamodb.Table('Analysis_Summaries')
        table.update_item(
            Key={'feedback_id': fid},
            UpdateExpression="SET #m = :val, #st = :proc",
            ExpressionAttributeValues={
                ':val': f"Master active. Routing {file_ext} path.",
                ':proc': "PROCESSING"
            },
            ExpressionAttributeNames={
                '#m': 'master',
                '#st': 'status'
            }
        )

        if file_ext == 'txt':
            # PATH A: DIRECT TEXT
            response = s3_client.get_object(Bucket=bucket, Key=key)
            raw_text = response['Body'].read().decode('utf-8')
            
            # Since we skip OCR, we mark 'text' here so UI knows input is ready
            table.update_item(
                Key={'feedback_id': fid},
                UpdateExpression="SET #t = :txt",
                ExpressionAttributeValues={':txt': raw_text},
                ExpressionAttributeNames={'#t': 'text'}
            )

            print(f"🚀 Master: Text detected. Triggering Analysis...")
            lambda_client.invoke(
                FunctionName='analysis_worker',
                InvocationType='Event',
                Payload=json.dumps({"feedback_id": fid, "text": raw_text})
            )
        else:
            # PATH B: IMAGE
            print(f"🚀 Master: Image detected. Triggering OCR Worker...")
            lambda_client.invoke(
                FunctionName='ocr_worker',
                InvocationType='Event',
                Payload=json.dumps(event)
            )

        return {"status": "orchestrated", "feedback_id": fid}

    except Exception as e:
        print(f"❌ Master Error: {str(e)}")
        return {"status": "error", "message": str(e)}