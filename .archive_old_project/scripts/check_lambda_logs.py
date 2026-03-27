import boto3
import time

def get_lambda_logs(function_name):
    client = boto3.client('logs', region_name='us-east-1')
    log_group = f'/aws/lambda/{function_name}'
    
    print(f"🕵️  Fetching logs for {function_name}...")
    
    try:
        # 1. Get the latest log stream
        streams = client.describe_log_streams(
            logGroupName=log_group,
            orderBy='LastEventTime',
            descending=True,
            limit=1
        )
        
        if not streams['logStreams']:
            print("❌ No log streams found. The Lambda likely never triggered.")
            return

        stream_name = streams['logStreams'][0]['logStreamName']
        
        # 2. Get the actual log events
        events = client.get_log_events(
            logGroupName=log_group,
            logStreamName=stream_name
        )
        
        print(f"\n📖 Latest Log Output ({stream_name}):\n" + "="*50)
        for event in events['events']:
            print(f"{event['message'].strip()}")
        print("="*50)

    except client.exceptions.ResourceNotFoundException:
        print(f"❌ Log group {log_group} not found. Did you deploy the Lambda?")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    get_lambda_logs("LabelWorker")