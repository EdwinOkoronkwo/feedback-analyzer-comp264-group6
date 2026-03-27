import boto3
import time

def auto_fix_pipeline():
    REGION = "us-east-1"
    TABLE_NAME = 'FeedbackData'
    
    db_client = boto3.client('dynamodb', region_name=REGION)
    lmb_client = boto3.client('lambda', region_name=REGION)

    print(f"🚀 Starting Auto-Discovery for {TABLE_NAME}...")

    # 1. Find the Lambda Function Name
    target_function = None
    try:
        functions = lmb_client.list_functions()
        for f in functions['Functions']:
            name = f['FunctionName']
            if 'analysis' in name.lower() and 'worker' in name.lower():
                target_function = name
                print(f"✅ Found Target Lambda: {target_function}")
                break
        
        if not target_function:
            print("❌ Error: Could not find a Lambda function with 'analysis' and 'worker' in the name.")
            return
    except Exception as e:
        print(f"❌ Failed to list functions: {e}")
        return

    # 2. Ensure Table Stream is Enabled
    try:
        table_info = db_client.describe_table(TableName=TABLE_NAME)
        stream_arn = table_info['Table'].get('LatestStreamArn')
        
        if not stream_arn:
            print(f"⚠️ Enabling Stream on {TABLE_NAME}...")
            db_client.update_table(
                TableName=TABLE_NAME,
                StreamSpecification={'StreamEnabled': True, 'StreamViewType': 'NEW_IMAGE'}
            )
            time.sleep(5) # Wait for AWS to propagate
            table_info = db_client.describe_table(TableName=TABLE_NAME)
            stream_arn = table_info['Table']['LatestStreamArn']
        print(f"📡 Stream ARN: {stream_arn}")
    except Exception as e:
        print(f"❌ Failed to access/update DynamoDB: {e}")
        return

    # 3. Check for existing mapping or create new one
    try:
        existing = lmb_client.list_event_source_mappings(
            EventSourceArn=stream_arn, 
            FunctionName=target_function
        )
        
        if existing['EventSourceMappings']:
            uuid = existing['EventSourceMappings'][0]['UUID']
            state = existing['EventSourceMappings'][0]['State']
            print(f"ℹ️ Trigger already exists (UUID: {uuid}). State: {state}")
            if state == 'Disabled':
                lmb_client.update_event_source_mapping(UUID=uuid, Enabled=True)
                print("🔄 Trigger was disabled. Enabling now...")
        else:
            print(f"🔗 Creating new Event Source Mapping...")
            response = lmb_client.create_event_source_mapping(
                EventSourceArn=stream_arn,
                FunctionName=target_function,
                Enabled=True,
                BatchSize=1,
                StartingPosition='LATEST'
            )
            print(f"✨ Success! Trigger Created. State: {response['State']}")

    except Exception as e:
        print(f"❌ Failed to create/update mapping: {e}")

if __name__ == "__main__":
    auto_fix_pipeline()