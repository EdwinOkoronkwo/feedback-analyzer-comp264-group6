import boto3
import zipfile
import io
import json

def combine_and_sync():
    REGION = "us-east-1"
    BUCKET = "comp264-edwin-1772030214"
    FUNCTION_NAME = "MasterWorker"
    lmb = boto3.client('lambda', region_name=REGION)
    s3 = boto3.client('s3', region_name=REGION)

    # --- 1. CLEANUP S3 ---
    print(f"🧹 Cleaning up 'verification' files in {BUCKET}...")
    objs = s3.list_objects_v2(Bucket=BUCKET, Prefix='live-data/verification_')
    if 'Contents' in objs:
        for obj in objs['Contents']:
            s3.delete_object(Bucket=BUCKET, Key=obj['Key'])
            print(f"  🗑️ Deleted {obj['Key']}")
    else:
        print("  ✅ No junk files found.")

    # --- 2. DEFINE FINAL LOGIC ---
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
            fid_obj = new_image.get('feedback_id') or new_image.get('id')
            feedback_id = fid_obj['S'] if fid_obj else "unknown"
            raw_text = new_image.get('text', {}).get('S', 'No content')
            
            # Analyze
            sentiment = comp.detect_sentiment(Text=raw_text[:4000], LanguageCode='en')['Sentiment']
            
            summary = "Summary unavailable"
            if mistral_key:
                try:
                    m_res = http.request('POST', "https://api.mistral.ai/v1/chat/completions",
                        headers={'Authorization': f'Bearer {mistral_key}', 'Content-Type': 'application/json'},
                        body=json.dumps({"model": "mistral-tiny", "messages": [{"role": "user", "content": f"Summarize in 5 words: {raw_text}"}]}),
                        timeout=4.0)
                    summary = json.loads(m_res.data)['choices'][0]['message']['content']
                except: pass

            # THE PAYLOAD (This must match the Dashboard expectations)
            payload = {
                "item": {
                    "feedback_id": feedback_id,
                    "text": raw_text,
                    "sentiment": sentiment,
                    "summary": summary,
                    "timestamp": datetime.datetime.now().isoformat()
                }
            }
            s3.put_object(Bucket=bucket, Key=f"live-data/{feedback_id.replace('/', '_')}.json", Body=json.dumps(payload))
            print(f"✅ Dispatched {feedback_id} to Dashboard S3")
    return {"status": "success"}
"""

    # --- 3. DEPLOY ---
    print(f"📤 Deploying Final Polished Logic to {FUNCTION_NAME}...")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        z.writestr('lambda_function.py', full_code)
    buf.seek(0)

    try:
        lmb.update_function_code(FunctionName=FUNCTION_NAME, ZipFile=buf.read())
        print("🚀 DEPLOYMENT COMPLETE. System is live!")
    except Exception as e:
        print(f"❌ Deployment failed: {e}")

if __name__ == "__main__":
    combine_and_sync()