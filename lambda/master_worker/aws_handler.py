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
        
        print(f"🎮 Master Worker: Routing {fid} (Type: {file_ext})")

        # 2. 📝 UI Status Update
        table = dynamodb.Table('Analysis_Summaries')
        table.update_item(
            Key={'feedback_id': fid},
            UpdateExpression="SET #m = :val, #st = :proc",
            ExpressionAttributeValues={
                ':val': f"Master active. Routing {file_ext} provider.",
                ':proc': "PROCESSING"
            },
            ExpressionAttributeNames={'#m': 'master', '#st': 'status'}
        )

        # --- MULTI-PROVIDER ROUTING ---

        if file_ext == 'tfrecord':
            # 📊 MULTI-PROVIDER LOGIC: NIST vs MNIST
            is_nist = "nist" in key.lower()
            dataset_type = "NIST_AUTHENTIC" if is_nist else "MNIST"
            resolution = [128, 128] if is_nist else [28, 28]

            print(f"✅ Master: {dataset_type} detected. Passing [ {resolution[0]}x{resolution[1]} ] to Analysis.")

            # 🚀 THE BATON PASS: Standardizing the Batch Payload
            lambda_client.invoke(
                FunctionName='analysis_worker',
                InvocationType='Event',
                Payload=json.dumps({
                    "feedback_id": fid,
                    "is_batch": True,
                    "dataset_type": dataset_type,
                    "resolution": resolution,  # 🎯 CRITICAL: Tells the loader how to reshape
                    "file_path": key,
                    "bucket": bucket
                })
            )

        elif file_ext in ['txt']:
            # ✍️ PROVIDER: DIRECT TEXT
            response = s3_client.get_object(Bucket=bucket, Key=key)
            raw_text = response['Body'].read().decode('utf-8')
            
            lambda_client.invoke(
                FunctionName='analysis_worker',
                InvocationType='Event',
                Payload=json.dumps({"feedback_id": fid, "text": raw_text})
            )

        elif file_ext in ['jpg', 'jpeg', 'png']:
            print(f"🚀 Master: Image detected. Routing to OCR...")
            # 🎯 FIX: Ensure we pass the record so OCR worker doesn't crash
            lambda_client.invoke(
                FunctionName='ocr_worker',
                InvocationType='Event',
                Payload=json.dumps(event) # This works because event contains 'Records'
            )
        return {"status": "orchestrated", "feedback_id": fid}

    except Exception as e:
        print(f"❌ Master Orchestration Error: {str(e)}")
        return {"status": "error", "message": str(e)}