import boto3
import zipfile
import io

def deploy_polished_master():
    lmb = boto3.client('lambda', region_name='us-east-1')
    
    full_code = """
import datetime
import json
import boto3
import os
import urllib3

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    comp = boto3.client('comprehend')
    http = urllib3.PoolManager()
    
    bucket = os.environ.get('S3_BUCKET_NAME')
    mistral_key = os.environ.get('MISTRAL_API_KEY')

    for record in event['Records']:
        if record['eventName'] == 'INSERT':
            new_image = record['dynamodb']['NewImage']
            feedback_id = (new_image.get('feedback_id') or new_image.get('id'))['S']
            raw_text = new_image.get('text', {}).get('S', 'No text')
            
            # 1. Sentiment Analysis
            sentiment_resp = comp.detect_sentiment(Text=raw_text[:4500], LanguageCode='en')
            sentiment = sentiment_resp['Sentiment']
            
            # 2. Mistral Summary
            summary = "Summary unavailable"
            if mistral_key:
                try:
                    m_url = "https://api.mistral.ai/v1/chat/completions"
                    m_body = json.dumps({
                        "model": "mistral-tiny",
                        "messages": [{"role": "user", "content": f"Summarize in 5 words: {raw_text}"}]
                    })
                    m_res = http.request('POST', m_url, 
                                         headers={'Authorization': f'Bearer {mistral_key}', 'Content-Type': 'application/json'},
                                         body=m_body, timeout=5.0)
                    summary = json.loads(m_res.data)['choices'][0]['message']['content']
                except:
                    summary = "Mistral Timeout"

            # 3. The "Complete Package" for S3
            payload = {
                "item": {
                    "feedback_id": feedback_id,
                    "text": raw_text,
                    "sentiment": sentiment,
                    "summary": summary,
                    "timestamp": datetime.datetime.now().isoformat()
                }
            }
            
            s3.put_object(
                Bucket=bucket, 
                Key=f"live-data/{feedback_id.replace('/', '_')}.json", 
                Body=json.dumps(payload)
            )
            
    return {"status": "success"}
"""

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        z.writestr('lambda_function.py', full_code)
    buf.seek(0)

    try:
        lmb.update_function_code(FunctionName='MasterWorker', ZipFile=buf.read())
        print("✨ MasterWorker Polished & Re-Deployed!")
    except Exception as e:
        print(f"❌ Deployment failed: {e}")

if __name__ == "__main__":
    deploy_polished_master()