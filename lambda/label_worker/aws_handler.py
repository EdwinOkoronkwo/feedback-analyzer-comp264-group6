import time
import os
import logging
import boto3

# Initialize AWS Clients
rekognition = boto3.client('rekognition')
dynamodb = boto3.resource('dynamodb')

# Set up logging for CloudWatch
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    AWS Label Worker: Uses Amazon Rekognition to identify objects.
    Triggered by S3 Upload event.
    """
    logger.info("🔔 AWS Label Worker Triggered via S3")

    try:
        # 1. Parse S3 Event (AWS specific structure)
        # This allows the worker to find the file automatically in the cloud
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key'] 
        
        # 🎯 Master ID Sync: Extracting feedback_id from the S3 Key prefix
        # Example Key: 550e8400_myphoto.jpg -> feedback_id = 550e8400
        feedback_id = key.split('_')[0]

        logger.info(f"📸 Identifying objects in S3: {bucket}/{key} for ID: {feedback_id}")

        # 2. Process with Amazon Rekognition
        # No local encoding or localhost requests needed
        response = rekognition.detect_labels(
            Image={
                'S3Object': {
                    'Bucket': bucket,
                    'Name': key
                }
            },
            MaxLabels=10,
            MinConfidence=75
        )

        # Extract labels into a simple list
        labels = [label['Name'] for label in response['Labels']]
        logger.info(f"🏷️ Labels found: {labels}")

        # 3. Save to AWS DynamoDB (Metadata Table)
        table_name = os.environ.get('METADATA_TABLE', 'Metadata')
        table = dynamodb.Table(table_name)
        
        table.put_item(Item={
            'feedback_id': feedback_id,
            'type': 'image_labels',
            'labels': labels,
            'engine': 'aws-rekognition',
            'processed_at': str(time.time()),
            's3_key': key
        })
        
        logger.info(f"✅ Successfully wrote labels to Cloud Metadata for: {feedback_id}")
        return {
            "status": "success", 
            "labels": labels, 
            "feedback_id": feedback_id
        }

    except Exception as e:
        logger.error(f"❌ Error in AWS Label Worker: {str(e)}")
        return {
            "status": "error", 
            "message": str(e), 
            "labels": []
        }