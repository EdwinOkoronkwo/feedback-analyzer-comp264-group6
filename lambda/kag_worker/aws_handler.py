import json
import boto3
import time
import os

# Initialize Resource
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Analysis_Summaries')

def lambda_handler(event, context):
    """
    KAG Worker: Hard-Coded for Error Visibility.
    If any key is missing, it kills the process and updates DynamoDB to FAILED.
    """
    # 1. 🔍 STRICT Parsing (No Fallbacks)
    fid = event.get('feedback_id') or event.get('id')
    bucket = event.get('bucket')
    image_url = event.get('image_url')
    s3_key = event.get('key')
    folder = event.get('folder')

    # 2. 🚨 CRITICAL ERROR: No ID
    if not fid:
        # We can't even update DynamoDB if we don't have the ID
        raise KeyError("FATAL: No 'feedback_id' or 'id' found in event payload. Chain Aborted.")

    # 3. 🚨 CRITICAL ERROR: S3 Path Failure
    if not s3_key and image_url:
        # Robust extraction attempt
        if "s3://" in image_url:
            path_stripped = image_url.replace("s3://", "")
            parts = path_stripped.split("/", 1)
            if len(parts) > 1:
                s3_key = parts[1]
    
    # Check if we still have nothing
    if not s3_key or not bucket:
        error_msg = f"MISSING_LOCATION: Bucket ({bucket}) or Key ({s3_key}) is null. URL provided: {image_url}"
        table.update_item(
            Key={'feedback_id': fid},
            UpdateExpression="SET #s = :s, master_log = :m, error_msg = :e",
            ExpressionAttributeNames={'#s': 'status'},
            ExpressionAttributeValues={
                ':s': 'FAILED',
                ':m': 'KAG Worker stopped: S3 Location error.',
                ':e': error_msg
            }
        )
        raise ValueError(error_msg)

    try:
        print(f"🏛️ KAG Worker: Processing {fid} for {folder}")

        # 4. 📝 SEED DYNAMODB
        # We only do this if the data is valid
        table.put_item(Item={
            'feedback_id': fid,
            'status': 'PROCESSING', 
            'dataset_type': f'KAG_{str(folder).upper()}',
            'image_path': f"s3://{bucket}/{s3_key}",
            'timestamp': str(time.time()),
            'master_log': f"KAG Worker validated {fid}. Handoff to OCR initiated."
        })

        # 5. 🚀 RETURN FOR STEP FUNCTION
        # If any of these are missing, the Step Function ASL will fail on the next step
        return {
            "feedback_id": fid,
            "bucket": bucket,
            "key": s3_key,
            "folder": folder,
            "status": "READY_FOR_OCR"
        }

    except Exception as e:
        error_trace = f"🛑 [KAG EXECUTION ERROR] {str(e)}"
        table.update_item(
            Key={'feedback_id': fid},
            UpdateExpression="SET #s = :s, master_log = :m",
            ExpressionAttributeNames={'#s': 'status'},
            ExpressionAttributeValues={
                ':s': 'FAILED', 
                ':m': error_trace
            }
        )
        raise e