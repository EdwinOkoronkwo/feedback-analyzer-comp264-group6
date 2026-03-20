import os
import json
import boto3
import urllib3
from datetime import datetime
from dotenv import load_dotenv

# Load local environment variables
load_dotenv()

def mock_lambda_handler(event):
    """
    This is a copy of your Lambda logic. 
    Running it here lets us see the errors in the terminal immediately.
    """
    print("🎬 Starting Mock Lambda Execution...")
    
    # Initialize Clients
    s3 = boto3.client('s3')
    comp = boto3.client('comprehend', region_name='us-east-1')
    trans = boto3.client('translate', region_name='us-east-1')
    http = urllib3.PoolManager()
    
    bucket = os.environ.get('S3_BUCKET_NAME')
    mistral_key = os.environ.get('MISTRAL_API_KEY')

    for record in event['Records']:
        if record['eventName'] == 'INSERT':
            # 1. Extract Data from Mock Event
            new_image = record['dynamodb']['NewImage']
            raw_text = new_image['text']['S']
            feedback_id = new_image['feedback_id']['S']
            print(f"📥 Processing Feedback ID: {feedback_id}")
            
            # 2. Translation
            print("🌐 Calling AWS Translate...")
            translated = trans.translate_text(
                Text=raw_text, SourceLanguageCode='auto', TargetLanguageCode='en'
            )['TranslatedText']
            
            # 3. Sentiment (Comprehend)
            print("📊 Calling AWS Comprehend...")
            sentiment = comp.detect_sentiment(
                Text=translated, LanguageCode='en'
            )['Sentiment']
            
            # 4. Summary (Mistral)
            print("🤖 Calling Mistral API...")
            summary = "Summary unavailable"
            if mistral_key:
                m_url = "https://api.mistral.ai/v1/chat/completions"
                m_body = json.dumps({
                    "model": "mistral-tiny",
                    "messages": [{"role": "user", "content": f"Summarize in 10 words: {translated}"}]
                })
                m_res = http.request('POST', m_url, 
                                     headers={'Authorization': f'Bearer {mistral_key}', 'Content-Type': 'application/json'},
                                     body=m_body)
                summary = json.loads(m_res.data)['choices'][0]['message']['content']

            # 5. S3 Push (The Dashboard Bridge)
            print(f"📤 Pushing to S3 Bucket: {bucket}")
            analytics_payload = {
                "item": {
                    "feedback_id": feedback_id,
                    "sentiment": {"s": sentiment},
                    "summary": summary,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            s3.put_object(
                Bucket=bucket, 
                Key=f"live-data/{feedback_id}.json", 
                Body=json.dumps(analytics_payload)
            )
            print(f"✅ Success! File created: live-data/{feedback_id}.json")

# --- MOCK EVENT SETUP ---
if __name__ == "__main__":
    mock_event = {
        "Records": [
            {
                "eventName": "INSERT",
                "dynamodb": {
                    "NewImage": {
                        "feedback_id": {"S": f"script_test_{datetime.now().strftime('%H%M%S')}"},
                        "text": {"S": "The product is excellent, but I wish the documentation was clearer."},
                        "timestamp": {"S": datetime.now().isoformat()}
                    }
                }
            }
        ]
    }
    
    try:
        mock_lambda_handler(mock_event)
    except Exception as e:
        print(f"❌ MOCK EXECUTION FAILED: {e}")