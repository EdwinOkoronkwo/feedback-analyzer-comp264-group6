import json
import boto3
import os
import urllib.parse
import time

# Initialize Clients
s3_client = boto3.client('s3')
sfn = boto3.client('stepfunctions')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Analysis_Summaries')

def lambda_handler(event, context):
    feedback_id = "UNKNOWN" 
    try:
        # 1. Parse Event
        record = event['Records'][0]
        bucket = record['s3']['bucket']['name']
        key = urllib.parse.unquote_plus(record['s3']['object']['key'])
        
        # 2. Extract Metadata Handshake
        head = s3_client.head_object(Bucket=bucket, Key=key)
        metadata = head.get('Metadata', {})
        feedback_id = metadata.get('feedback-id') or metadata.get('feedback_id')

        if not feedback_id:
            print(f"❌ METADATA ERROR: No ID for {key}")
            return {"statusCode": 400}

        # 3. 📝 LOG START
        table.update_item(
            Key={'feedback_id': feedback_id},
            UpdateExpression="SET #s = :s, master_log = :m, timestamp = :t",
            ExpressionAttributeNames={'#s': 'status'},
            ExpressionAttributeValues={
                ':s': 'SFN_STARTING',
                ':m': f"Master detected file. Attempting SFN trigger for {key}...",
                ':t': str(time.time())
            }
        )

        # 4. 🚀 TRIGGER STEP FUNCTION
        input_payload = {
            "feedback_id": feedback_id,
            "bucket": bucket,
            "key": key
        }
        
        response = sfn.start_execution(
            stateMachineArn=os.environ['STATE_MACHINE_ARN'],
            input=json.dumps(input_payload)
        )
        
        # 5. LOG SUCCESS
        table.update_item(
            Key={'feedback_id': feedback_id},
            UpdateExpression="SET #s = :s, master_log = :m, execution_arn = :arn",
            ExpressionAttributeNames={'#s': 'status'},
            ExpressionAttributeValues={
                ':s': 'SFN_RUNNING',
                ':m': "🚀 Step Function started successfully.",
                ':arn': response['executionArn']
            }
        )

        return {"statusCode": 200}

    except Exception as e:
        error_trace = f"🛑 MASTER CRASH: {str(e)}"
        print(error_trace)
        if feedback_id != "UNKNOWN":
            table.update_item(
                Key={'feedback_id': feedback_id},
                UpdateExpression="SET #s = :s, master_log = :m",
                ExpressionAttributeNames={'#s': 'status'},
                ExpressionAttributeValues={':s': 'FAILED', ':m': error_trace}
            )
        raise e