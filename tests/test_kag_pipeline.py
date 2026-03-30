import boto3
import time
import os
import json

from implementations.aws.bridge.aws_bridge import AWSPipelineBridge

# Imports from your project structure


# --- CONFIGURATION ---
BUCKET_NAME = 'comp264-edwin-1772030214'
TABLE_SUMMARIES = 'Analysis_Summaries'
REGION = 'us-east-1'

# Path to your extracted Kaggle Tobacco dataset
KAG_BASE_PATH = "data/kag_reviews/dataset"

# Initialize AWS Clients
dynamodb = boto3.resource('dynamodb', region_name=REGION)
table = dynamodb.Table(TABLE_SUMMARIES)

def poll_until_done(fid, timeout=120, mode="KAG_BATCH"):
    """
    Wait for a specific feedback_id to reach terminal status in DynamoDB.
    Terminal status is defined by 'speech_status' == 'COMPLETED'.
    """
    print(f"⏳ Monitoring Pipeline for {fid} ({mode})...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        time.sleep(3) # Real docs take longer to process than MNIST
        try:
            item = table.get_item(Key={'feedback_id': fid}).get('Item')
            if item:
                # Check for the final step in the pipeline
                status = item.get('speech_status')
                if status == 'COMPLETED':
                    summary = item.get('summary', 'No summary found')
                    print(f"✨ [DONE] {fid} | Category: {item.get('dataset_type')} | Summary: {summary[:70]}...")
                    return True
                
                # Check for failures early
                pipeline_status = item.get('status')
                if "FAILED" in str(pipeline_status):
                    print(f"❌ [FAIL] {fid} reached error state: {pipeline_status}")
                    return False
                    
        except Exception as e:
            print(f"⚠️ Error polling DynamoDB: {str(e)}")
            
    print(f"❌ Timeout reached for {fid}")
    return False

def run_kag_tests(folder="Email", batch_limit=5):
    bridge = AWSPipelineBridge()

    print(f"\n📧 === PHASE 5: KAG_TOBACCO FULL PIPELINE ({batch_limit} samples from {folder}) ===")

    if os.path.exists(KAG_BASE_PATH):
        # Trigger the specialized Kaggle ingestion logic
        res_kag = bridge.trigger_kag_ingestion(
            base_path=KAG_BASE_PATH, 
            folder_name=folder,
            limit=batch_limit
        )
        
        sample_ids = res_kag.get('sample_ids', [])
        print(f"✅ Bridge triggered {len(sample_ids)} real documents.")

        success_count = 0
        for fid in sample_ids:
            print(f"🖼️  Local Sample: samples/{fid}.jpg")
            if poll_until_done(fid, mode="KAG_DOC"):
                success_count += 1
        
        print(f"\n📊 KAG TEST SUMMARY: {success_count}/{len(sample_ids)} documents processed.")
    else:
        print(f"⚠️ Kaggle data not found at {KAG_BASE_PATH}. Please check folder structure.")

if __name__ == "__main__":
    # Ensure local imports work correctly
    import sys
    sys.path.append(os.getcwd())
    
    # Start with a small batch to verify the handoff
    run_kag_tests(folder="Email", batch_limit=5)