import boto3
import json

def lambda_handler(event, context):
    rekognition = boto3.client('rekognition')
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('FeedbackData') # Your DynamoDB Table Name

    # 1. Get the bucket and key from the S3 Event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']

    # 2. Call Amazon Rekognition
    response = rekognition.detect_labels(
        Image={'S3Object': {'Bucket': bucket, 'Name': key}},
        MaxLabels=10
    )

    # 3. Extract the ID from the filename (we saved it as f"{uuid}-{name}")
    # We need this ID to find the record in DynamoDB
    record_id = key.split('/')[-1].split('-')[0]

    # 4. Update DynamoDB with the labels found in the image
    labels = [label['Name'] for label in response['Labels']]
    table.update_item(
        Key={'id': record_id},
        UpdateExpression="set image_labels = :l",
        ExpressionAttributeValues={':l': labels}
    )

    return {"status": "success", "labels": labels}