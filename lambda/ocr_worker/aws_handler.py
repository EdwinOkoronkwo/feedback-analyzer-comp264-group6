import boto3
import json

# 🎯 FIX 1: Explicitly set the region to match your bucket
REGION = 'us-east-1' 
textract = boto3.client('textract', region_name=REGION)
s3_client = boto3.client('s3', region_name=REGION)
dynamodb = boto3.resource('dynamodb', region_name=REGION)

# --- OCR LAMBDA ---
def lambda_handler(event, context):
    fid = event.get('feedback_id')
    bucket = event.get('bucket')
    key = event.get('key')
    table = dynamodb.Table('Analysis_Summaries')

    try:
        # Pre-flight check
        s3_client.head_object(Bucket=bucket, Key=key)

        response = textract.detect_document_text(
            Document={'S3Object': {'Bucket': bucket, 'Name': key}}
        )

        raw_text = " ".join([item['Text'] for item in response['Blocks'] if item['BlockType'] == 'LINE'])

        # Success update
        table.update_item(
            Key={'feedback_id': fid},
            UpdateExpression="SET #s = :stat, master_log = :m",
            ExpressionAttributeNames={'#s': 'status'},
            ExpressionAttributeValues={
                ':stat': 'OCR_COMPLETED',
                ':m': 'OCR Success: Text extracted.'
            }
        )
        return {**event, "raw_text": raw_text, "status": "OCR_SUCCESS"}

    except Exception as e:
        error_msg = f"❌ OCR FAILURE: {str(e)}"
        print(error_msg)
        
        # 🎯 THE TERMINAL VISIBILITY FIX
        # We write the error message into 'master_log' so your Streamlit 
        # terminal prints it in the 'Keys' or 'Status' debug line.
        table.update_item(
            Key={'feedback_id': fid},
            UpdateExpression="SET #s = :stat, master_log = :err",
            ExpressionAttributeNames={'#s': 'status'},
            ExpressionAttributeValues={
                ':stat': 'FAILED',
                ':err': error_msg
            }
        )
        raise e # Still raise so the Step Function knows it failed