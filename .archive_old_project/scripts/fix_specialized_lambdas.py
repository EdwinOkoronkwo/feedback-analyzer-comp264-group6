import boto3
import time

def fix_specialized_workers():
    REGION = "us-east-1"
    TABLE_NAME = 'FeedbackData'
    # The two workers that need to 'hear' the feedback
    WORKER_NAMES = ['SummaryWorker', 'TranslateWorker']
    
    db_client = boto3.client('dynamodb', region_name=REGION)
    lmb_client = boto3.client('lambda', region_name=REGION)

    print(f"🚀 Connecting specialized workers to {TABLE_NAME}...")

    # 1. Get the Stream ARN
    try:
        table_info = db_client.describe_table(TableName=TABLE_NAME)
        stream_arn = table_info['Table'].get('LatestStreamArn')
        
        if not stream_arn:
            print("⚠️ Streams not enabled. Enabling...")
            db_client.update_table(
                TableName=TABLE_NAME,
                StreamSpecification={'StreamEnabled': True, 'StreamViewType': 'NEW_IMAGE'}
            )
            time.sleep(5)
            stream_arn = db_client.describe_table(TableName=TABLE_NAME)['Table']['LatestStreamArn']
        print(f"📡 Stream ARN: {stream_arn}")
    except Exception as e:
        print(f"❌ Table Error: {e}")
        return

    # 2. Connect each worker
    for worker in WORKER_NAMES:
        print(f"🔗 Checking {worker}...")
        try:
            # Check if mapping already exists
            existing = lmb_client.list_event_source_mappings(
                EventSourceArn=stream_arn, 
                FunctionName=worker
            )
            
            if not existing['EventSourceMappings']:
                lmb_client.create_event_source_mapping(
                    EventSourceArn=stream_arn,
                    FunctionName=worker,
                    Enabled=True,
                    BatchSize=1,
                    StartingPosition='LATEST'
                )
                print(f"  ✅ Trigger Created for {worker}")
            else:
                print(f"  ℹ️ {worker} is already connected.")
                
        except Exception as e:
            print(f"  ❌ Failed to connect {worker}: {e}")

if __name__ == "__main__":
    fix_specialized_workers()