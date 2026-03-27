import os
import json
import boto3
import requests
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def test_full_pipeline_logic():
    print("🚀 Testing Full Analysis Chain...")
    
    text = "The service was great, but the delivery took three weeks."
    bucket = os.environ.get("S3_BUCKET_NAME")
    mistral_key = os.environ.get("MISTRAL_API_KEY")

    # 1. AWS Comprehend (Sentiment)
    try:
        comp = boto3.client('comprehend', region_name='us-east-1')
        sent_res = comp.detect_sentiment(Text=text, LanguageCode='en')
        sentiment = sent_res['Sentiment']
        print(f"✅ Sentiment: {sentiment}")
    except Exception as e:
        print(f"❌ Comprehend Failed: {e}")
        return

    # 2. Mistral (Summary)
    try:
        url = "https://api.mistral.ai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {mistral_key}"}
        payload = {
            "model": "mistral-tiny",
            "messages": [{"role": "user", "content": f"Summarize in 5 words: {text}"}]
        }
        m_res = requests.post(url, json=payload, headers=headers)
        summary = m_res.json()['choices'][0]['message']['content']
        print(f"✅ Mistral Summary: {summary}")
    except Exception as e:
        print(f"❌ Mistral Failed: {e}")
        return

    # 3. S3 Live-Data Push (The Dashboard Fix)
    try:
        s3 = boto3.client('s3')
        test_id = f"test_{int(datetime.now().timestamp())}"
        analytics_payload = {
            "item": {
                "feedback_id": test_id,
                "sentiment": {"s": sentiment},
                "summary": summary,
                "timestamp": datetime.now().isoformat()
            }
        }
        s3.put_object(
            Bucket=bucket,
            Key=f"live-data/{test_id}.json",
            Body=json.dumps(analytics_payload)
        )
        print(f"✅ S3 Live-Data: Uploaded to s3://{bucket}/live-data/{test_id}.json")
    except Exception as e:
        print(f"❌ S3 Upload Failed: {e}")

if __name__ == "__main__":
    test_full_pipeline_logic()