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
    MNIST Ingestor Worker: Standardizes MNIST batch samples into the main Feedback Pipeline.
    Location: /home/edwin/projects/feedback_analyzer/lambda/mnist_ingestor_worker/aws_handler.py
    """
    fid = event.get('feedback_id', f"mnist_batch_{int(time.time())}")
    table = dynamodb.Table('Analysis_Summaries')
    
    try:
        # 1. Extract Data from Bridge Payload
        label = event.get('label', 'Unknown')
        image_url = event.get('image_url', '')
        
        # We format the 'raw_text' so the Analysis & Summary workers have context
        raw_text = f"MNIST Classification: The handwritten image represents the digit {label}."

        print(f"🔢 [MNIST_INGESTOR] Processing Sample {fid} (Label: {label})")

        # 2. 📝 UI ALIGNMENT: Initialize the Analysis_Summaries table
        # We set status to OCR_COMPLETED to bypass Textract and turn the 📸 light GREEN.
        table.put_item(Item={
            'feedback_id': fid,
            'status': 'OCR_COMPLETED',
            'dataset_type': 'MNIST',
            'raw_text': raw_text,
            'image_path': image_url,
            'timestamp': str(int(time.time())),
            'master': f"MNIST Ingestor: Digit '{label}' detected. Bypassing OCR."
        })

        # 3. 🎯 THE BATON PASS: Trigger Analysis Worker
        analysis_payload = {
            "feedback_id": fid,
            "text": raw_text
        }

        print(f"🚀 [MNIST_INGESTOR] Passing Baton to analysis_worker for {fid}...")
        
        lambda_client.invoke(
            FunctionName='analysis_worker',
            InvocationType='Event',
            Payload=json.dumps(analysis_payload).encode('utf-8')
        )

        return {
            "status": "success",
            "feedback_id": fid,
            "next_step": "analysis_worker_triggered"
        }

    except Exception as e:
        print(f"❌ [MNIST_INGESTOR] Error for {fid}: {str(e)}")
        # Update DynamoDB with failure so the UI doesn't hang on 'Processing'
        try:
            table.update_item(
                Key={'feedback_id': fid},
                UpdateExpression="set #s = :err, #m = :msg",
                ExpressionAttributeNames={'#s': 'status', '#m': 'master'},
                ExpressionAttributeValues={':err': 'INGEST_FAILED', ':msg': str(e)}
            )
        except:
            pass
            
        return {"status": "error", "message": str(e)}