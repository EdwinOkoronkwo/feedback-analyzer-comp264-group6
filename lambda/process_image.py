import boto3
import json

def lambda_handler(event, context):
    # 1. Setup Providers
    vision = VisionProvider()
    translator = TranslationProvider() # Your existing translator
    
    # 2. Extract S3 Info
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    feedback_id = key.split('_')[0]

    # 3. Parallel Processing
    labels = vision.detect_labels(bucket, key)
    raw_ocr = vision.extract_text(bucket, key)
    
    translated_ocr = None
    if raw_ocr:
        translated_ocr = translator.translate(raw_ocr)

    # 4. Save everything to ONE table
    db = boto3.resource('dynamodb')
    db.Table('FeedbackMedia').put_item(
        Item={
            'feedback_id': feedback_id,
            'labels': labels,
            'ocr_text': raw_ocr,
            'ocr_translated': translated_ocr,
            'image_url': f"https://{bucket}.s3.amazonaws.com/{key}"
        }
    )