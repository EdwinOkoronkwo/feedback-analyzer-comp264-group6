import boto3
import time
import sys

# --- CONFIGURATION ---
FUNCTION_NAME = "kag_worker"  # The Lambda that is stuck
REGION = "us-east-1"
# ---------------------

def tail_lambda_logs(function_name):
    client = boto3.client('logs', region_name=REGION)
    log_group = f"/aws/lambda/{function_name}"
    
    print(f"📡 Connecting to {log_group}...")
    
    try:
        # 1. Get the most recent log stream
        streams = client.describe_log_streams(
            logGroupName=log_group,
            orderBy='LastEventTime',
            descending=True,
            limit=1
        )
        
        if not streams.get('logStreams'):
            print("❌ No logs found. Has the Lambda ever run?")
            return

        stream_name = streams['logStreams'][0]['logStreamName']
        print(f"🔍 Snipping Stream: {stream_name}\n" + "="*50)

        # 2. Fetch the last 30 events
        response = client.get_log_events(
            logGroupName=log_group,
            logStreamName=stream_name,
            limit=30,
            startFromHead=False
        )
        
        for event in response['events']:
            msg = event['message'].strip()
            
            # Color-code errors for Cursor Terminal
            if "ERROR" in msg or "Exception" in msg or "Traceback" in msg:
                print(f"\033[91m🛑 [AWS ERROR] {msg}\033[0m")
            elif "Task timed out" in msg:
                print(f"\033[93m⚠️ [TIMEOUT] {msg}\033[0m")
            else:
                print(f"ℹ️ {msg}")
                
        print("="*50 + "\n✅ Check the red lines above for the fix.")

    except Exception as e:
        print(f"❌ Failed to fetch logs: {e}")

if __name__ == "__main__":
    tail_lambda_logs(FUNCTION_NAME)