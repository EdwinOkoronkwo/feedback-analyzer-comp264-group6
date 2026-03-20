import boto3
import time
import uuid
import os
import json

# --- CONFIGURATION ---
BUCKET_NAME = 'comp264-edwin-1772030214'
TABLE_SUMMARIES = 'Analysis_Summaries'
REGION = 'us-east-1'

s3 = boto3.client('s3', region_name=REGION)
dynamodb = boto3.resource('dynamodb', region_name=REGION)
lambda_client = boto3.client('lambda', region_name=REGION)
table = dynamodb.Table(TABLE_SUMMARIES)

def poll_until_done(fid, timeout=60):
    """Wait for a specific feedback_id to reach COMPLETED status."""
    print(f"⏳ Monitoring Relay for {fid}...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        time.sleep(2)
        item = table.get_item(Key={'feedback_id': fid}).get('Item')
        
        if item:
            status = item.get('speech_status')
            if status == 'COMPLETED':
                print(f"✨ [DONE] {fid}")
                print(f"   Summary: {item.get('summary')}")
                print(f"   Audio:   {item.get('audio_path')}\n")
                return True
            elif item.get('sentiment'):
                print(f"   ...Processing (Sentiment: {item.get('sentiment')})")
        else:
            print(f"   ...Waiting for OCR/Initial Analysis")
            
    print(f"❌ Timeout reached for {fid}")
    return False

def run_sequential_tests(image_path, raw_text):
    # --- PHASE 1: IMAGE FEEDBACK ---
    print("📸 === PHASE 1: TESTING IMAGE FEEDBACK (OCR) ===")
    if os.path.exists(image_path):
        img_fid = f"img_{uuid.uuid4().hex[:8]}"
        ext = image_path.split('.')[-1]
        print(f"🚀 Uploading {image_path} to S3...")
        s3.upload_file(image_path, BUCKET_NAME, f"uploads/{img_fid}.{ext}")
        poll_until_done(img_fid)
    else:
        print(f"⚠️ Image {image_path} not found. Skipping Phase 1.")

    # --- PHASE 2: TEXT FEEDBACK ---
    print("✍️ === PHASE 2: TESTING DIRECT TEXT FEEDBACK ===")
    txt_fid = f"txt_{uuid.uuid4().hex[:8]}"
    print(f"🚀 Invoking Analysis Worker directly with text...")
    
    payload = {
        "feedback_id": txt_fid,
        "text": raw_text
    }
    
    lambda_client.invoke(
        FunctionName='analysis_worker',
        InvocationType='Event',
        Payload=json.dumps(payload).encode('utf-8')
    )
    poll_until_done(txt_fid)

    print("🏁 Sequential test run finished.")

if __name__ == "__main__":
    # Settings
    IMAGE_TO_TEST = "sample_feedback.jpg"
    TEXT_TO_TEST = "The service was great, but the delivery took forever. Very mixed feelings."
    
    run_sequential_tests(IMAGE_TO_TEST, TEXT_TO_TEST)