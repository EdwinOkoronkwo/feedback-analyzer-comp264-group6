import boto3
import os

comprehend = boto3.client('comprehend')
# 1. Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

def lambda_handler(event, context):
    text = event.get('text', '')
    fid = event.get('feedback_id')
    table_name = 'Analysis_Summaries'

    if not text:
        return {**event, "sentiment": "NEUTRAL", "status": "NO_TEXT_FOR_ANALYSIS"}

    try:
        # Detect Sentiment
        response = comprehend.detect_sentiment(
            Text=text[:5000], 
            LanguageCode='en'
        )
        
        sentiment = response['Sentiment']

        # 2. 🎯 THE MISSING PIECE: Update the Table
        table = dynamodb.Table(table_name)
        table.update_item(
            Key={'feedback_id': fid},
            UpdateExpression="SET #s = :stat, sentiment = :sent",
            ExpressionAttributeNames={'#s': 'status'},
            ExpressionAttributeValues={
                ':stat': 'COMPLETED',  # <--- This breaks the Streamlit Loop!
                ':sent': sentiment
            }
        )

        # 3. Return to Step Function so the next worker can use it
        return {
            **event,
            "sentiment": sentiment,
            "sentiment_score": response['SentimentScore'],
            "status": "COMPLETED" 
        }
    except Exception as e:
        print(f"❌ Analysis Error: {str(e)}")
        raise e