import boto3

def connect_master_worker():
    lmb = boto3.client('lambda', region_name='us-east-1')
    db = boto3.client('dynamodb', region_name='us-east-1')
    
    # Get the Stream ARN again
    stream_arn = db.describe_table(TableName='FeedbackData')['Table']['LatestStreamArn']
    
    print(f"🔗 Connecting MasterWorker to stream...")
    try:
        lmb.create_event_source_mapping(
            EventSourceArn=stream_arn,
            FunctionName='MasterWorker',
            Enabled=True,
            BatchSize=1,
            StartingPosition='LATEST'
        )
        print("✅ MasterWorker is now live!")
    except Exception as e:
        print(f"ℹ️ MasterWorker connection status: {e}")

if __name__ == "__main__":
    connect_master_worker()