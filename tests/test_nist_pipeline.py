import boto3
import time
import uuid
import os
import json
import tensorflow as tf

# Imports from your project structure
from scripts.mnist_loader import get_mnist_dataset
from chalicelib.ingestion.nist_loader import get_prepared_nist_batch
from implementations.aws.bridge.aws_bridge import AWSPipelineBridge

# --- CONFIGURATION ---
BUCKET_NAME = 'comp264-edwin-1772030214'
TABLE_SUMMARIES = 'Analysis_Summaries'
REGION = 'us-east-1'

# Local Paths to your TFRecords
MNIST_TFRECORD = "data/tfrecords/mnist_standard.tfrecord"
NIST_TFRECORD = "data/tfrecords/nist_authentic.tfrecord" 

# Initialize AWS Clients
s3 = boto3.client('s3', region_name=REGION)
dynamodb = boto3.resource('dynamodb', region_name=REGION)
lambda_client = boto3.client('lambda', region_name=REGION)
table = dynamodb.Table(TABLE_SUMMARIES)

def poll_until_done(fid, timeout=90, mode="STANDARD"):
    """
    Wait for a specific feedback_id to reach terminal status in DynamoDB.
    Terminal status is defined by 'speech_status' == 'COMPLETED'.
    """
    print(f"⏳ Monitoring Relay for {fid} ({mode})...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        time.sleep(2)
        try:
            item = table.get_item(Key={'feedback_id': fid}).get('Item')
            if item:
                # Check for the final step in the pipeline
                status = item.get('speech_status')
                if status == 'COMPLETED':
                    summary = item.get('summary', 'No summary found')
                    print(f"✨ [DONE] {fid} | Summary: {summary[:60]}...")
                    return True
        except Exception as e:
            print(f"⚠️ Error polling DynamoDB: {str(e)}")
            
    print(f"❌ Timeout reached for {fid}")
    return False

def run_comprehensive_tests(image_path, raw_text, mnist_path, nist_path, batch_limit=2):
    bridge = AWSPipelineBridge()

    # --- PHASE 1: IMAGE FEEDBACK (OCR) ---
    print("\n📸 === PHASE 1: TESTING IMAGE FEEDBACK (OCR) ===")
    if os.path.exists(image_path):
        img_fid = f"img_{uuid.uuid4().hex[:8]}"
        print(f"🚀 Uploading {image_path} to S3...")
        s3.upload_file(image_path, BUCKET_NAME, f"uploads/{img_fid}.jpg")
        poll_until_done(img_fid)
    else:
        print(f"⚠️ Image {image_path} not found. Skipping Phase 1.")

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

    # --- PHASE 3: MNIST FULL PIPELINE TEST ---
    print(f"\n🔢 === PHASE 3: MNIST FULL PIPELINE ({batch_limit} samples) ===")
    # get_mnist_dataset returns the object required by the bridge
    mnist_dataset = get_mnist_dataset(mnist_path, batch_size=1)
    
    res_mnist = bridge.trigger_dataset_ingestion({
        'limit': batch_limit,
        'dataset': mnist_dataset
    })
    
    for fid in res_mnist.get('sample_ids', []):
        poll_until_done(fid, mode="MNIST_BATCH")

    # --- PHASE 4: NIST AUTHENTIC FULL PIPELINE ---
    print(f"\n🏛️ === PHASE 4: NIST AUTHENTIC FULL PIPELINE ({batch_limit} samples) ===")

    if os.path.exists(nist_path):
        from chalicelib.ingestion.nist_loader import parse_nist_record

        # 🎯 THE FIX: You MUST .map() the parser so 'record' becomes a dictionary
        nist_ds_object = tf.data.TFRecordDataset(nist_path).map(parse_nist_record)

        # Now pass the PARSED object to the bridge
        res_nist = bridge.trigger_nist_ingestion(
            dataset=nist_ds_object, 
            limit=batch_limit
        )
        for fid in res_nist.get('sample_ids', []):
            poll_until_done(fid, mode="NIST_BATCH")
    else:
        print(f"⚠️ NIST TFRecord not found at {nist_path}. Skipping Phase 4.")

    print("\n🏁 Full-Chain Multi-Modal Cloud test finished.")

if __name__ == "__main__":
    # Test Data Settings
    IMAGE_TO_TEST = "sample_feedback.jpg"
    TEXT_TO_TEST = "The service was great, but the delivery took forever. Very mixed feelings."
    
    # --- 🍞 THE SANITY BAKE ---
    # If NIST_TFRECORD is missing or empty, create a single valid 128x128 record
    if not os.path.exists(NIST_TFRECORD) or os.path.getsize(NIST_TFRECORD) < 100:
        print("⚠️ NIST TFRecord is empty or missing. Baking a sanity record...")
        with tf.io.TFRecordWriter(NIST_TFRECORD) as writer:
            # Create a 128x128 float array (zeros)
            img_data = tf.zeros([128, 128], dtype=tf.float32).numpy().tobytes()
            example = tf.train.Example(features=tf.train.Features(feature={
                'image': tf.train.Feature(bytes_list=tf.train.BytesList(value=[img_data])),
                'label': tf.train.Feature(int64_list=tf.train.Int64List(value=[4])), # Dummy Label
            }))
            writer.write(example.SerializeToString())
        print(f"✅ Sanity record 'baked' at {NIST_TFRECORD}")

    # Ensure local imports work correctly
    import sys
    sys.path.append(os.getcwd())
    
    run_comprehensive_tests(
        IMAGE_TO_TEST, 
        TEXT_TO_TEST, 
        MNIST_TFRECORD, 
        NIST_TFRECORD, 
        batch_limit=20
    )