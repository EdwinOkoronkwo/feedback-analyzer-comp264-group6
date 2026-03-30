import boto3
import time
import uuid
import os
import json
from scripts.mnist_loader import get_mnist_dataset
from implementations.aws.bridge.aws_bridge import AWSPipelineBridge

# --- CONFIGURATION ---
BUCKET_NAME = 'comp264-edwin-1772030214'
TABLE_SUMMARIES = 'Analysis_Summaries'
REGION = 'us-east-1'
MNIST_TFRECORD = "data/tfrecords/mnist_standard.tfrecord"

s3 = boto3.client('s3', region_name=REGION)
dynamodb = boto3.resource('dynamodb', region_name=REGION)
lambda_client = boto3.client('lambda', region_name=REGION)
table = dynamodb.Table(TABLE_SUMMARIES)

def poll_until_done(fid, timeout=60, mode="STANDARD"):
    """Wait for a specific feedback_id to reach a terminal status."""
    print(f"⏳ Monitoring Relay for {fid} ({mode})...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        time.sleep(2)
        item = table.get_item(Key={'feedback_id': fid}).get('Item')
        
        if item:
            # For MNIST, we look for PROCESSED status
            if mode == "MNIST" and item.get('status') == 'PROCESSED':
                print(f"✨ [DONE] MNIST Sample {fid} | Label: {item.get('label')}")
                return True
            
            # For Text/OCR, we look for the speech_status COMPLETED
            status = item.get('speech_status')
            if status == 'COMPLETED':
                print(f"✨ [DONE] {fid} | Summary: {item.get('summary')[:50]}...")
                return True
        else:
            if mode != "MNIST":
                print(f"   ...Waiting for Initial Analysis")
            
    print(f"❌ Timeout reached for {fid}")
    return False

def run_comprehensive_tests(image_path, raw_text, mnist_path, batch_limit=2):
    # --- PHASE 1: IMAGE FEEDBACK (OCR) ---
    print("\n📸 === PHASE 1: TESTING IMAGE FEEDBACK (OCR) ===")
    if os.path.exists(image_path):
        img_fid = f"img_{uuid.uuid4().hex[:8]}"
        print(f"🚀 Uploading {image_path} to S3...")
        s3.upload_file(image_path, BUCKET_NAME, f"uploads/{img_fid}.jpg")
        poll_until_done(img_fid)
    else:
        print(f"⚠️ Image {image_path} not found.")

    # --- PHASE 2: TEXT FEEDBACK ---
    print("\n✍️ === PHASE 2: TESTING DIRECT TEXT FEEDBACK ===")
    txt_fid = f"txt_{uuid.uuid4().hex[:8]}"
    print(f"🚀 Invoking Analysis Worker with text...")
    payload = {"feedback_id": txt_fid, "text": raw_text}
    lambda_client.invoke(
        FunctionName='analysis_worker',
        InvocationType='Event',
        Payload=json.dumps(payload).encode('utf-8')
    )
    poll_until_done(txt_fid)

    # --- PHASE 3: MNIST BATCH FEEDBACK ---
    # --- PHASE 3: MNIST FULL PIPELINE TEST ---
    print(f"\n🔢 === PHASE 3: MNIST FULL PIPELINE ({batch_limit} samples) ===")
    dataset = get_mnist_dataset(mnist_path, batch_size=1)
    bridge = AWSPipelineBridge()
    
    res = bridge.trigger_dataset_ingestion({
        'limit': batch_limit,
        'dataset': dataset
    })
    
    # We now poll for EVERY sample to finish the ENTIRE cloud process
    for fid in res['sample_ids']:
        # We use mode="STANDARD" because we want to see summary/audio results
        poll_until_done(fid, timeout=90, mode="STANDARD") 

    print("\n🏁 Full-Chain Multi-Modal test finished.")
if __name__ == "__main__":
    # Settings
    IMAGE_TO_TEST = "sample_feedback.jpg"
    TEXT_TO_TEST = "The service was great, but the delivery took forever. Very mixed feelings."
    
    run_comprehensive_tests(IMAGE_TO_TEST, TEXT_TO_TEST, MNIST_TFRECORD, batch_limit=3)