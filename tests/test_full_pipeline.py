import sys
import os
import time
import json
import boto3
import requests  # Added missing import
import zipfile   # Added missing import
import io        # Added missing import
from boto3.dynamodb.conditions import Key

# --- 1. CONFIGURATION ---
BUCKET_NAME = "comp264-edwin-1772030214"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Note: Ensure this path matches your folder structure
TEST_FILE_PATH = os.path.join(BASE_DIR, "sample_images", "french.jpg")
TEST_ID = os.path.basename(TEST_FILE_PATH)

# AWS Clients
s3 = boto3.client('s3')
db = boto3.resource('dynamodb', region_name="us-east-1")
logs_client = boto3.client('logs', region_name="us-east-1")
lambda_client = boto3.client('lambda', region_name="us-east-1")

def verify_lambda_source(function_name):
    """Downloads the actual active code from AWS and prints the loop logic."""
    print(f"\n📡 FETCHING LIVE SOURCE CODE FOR: {function_name}...")
    try:
        # 1. Get the deployment package URL
        response = lambda_client.get_function(FunctionName=function_name)
        code_url = response['Code']['Location']
        
        # 2. Download and unzip in memory
        r = requests.get(code_url)
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            for file_name in z.namelist():
                if file_name.endswith('.py'):
                    print(f"📄 Found Source File: {file_name}")
                    content = z.read(file_name).decode('utf-8')
                    
                    if "target_langs" in content:
                        print("✅ VERIFIED: Multi-language loop exists in live code.")
                    else:
                        print("❌ ALERT: The live code is MISSING the loop logic!")
                    
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if "target_langs" in line or "table.put_item" in line:
                            print(f"    Line {i+1}: {line.strip()}")
    except Exception as e:
        print(f"❌ Could not verify source: {str(e)}")

def get_latest_logs(function_name):
    log_group = f"/aws/lambda/{function_name}"
    print(f"\n🔍 FETCHING CLOUDWATCH LOGS FOR: {function_name}...")
    try:
        streams = logs_client.describe_log_streams(
            logGroupName=log_group, orderBy='LastEventTime', descending=True, limit=1
        )
        if not streams['logStreams']:
            print("⚠️ No log streams found.")
            return

        stream_name = streams['logStreams'][0]['logStreamName']
        events = logs_client.get_log_events(
            logGroupName=log_group, logStreamName=stream_name, limit=10
        )
        for event in events['events']:
            print(f"🕒 {time.ctime(event['timestamp']/1000)} | {event['message'].strip()}")
    except Exception as e:
        print(f"❌ Could not fetch logs: {str(e)}")

def run_full_test():
    # --- STEP 0: Verify what code is actually on AWS ---
    verify_lambda_source("translate_worker")
    
    print(f"\n🚀 STARTING PROGRAMMATIC UPLOAD TEST: {TEST_ID}")
    print("="*60)

    # 1. S3 Upload
    if not os.path.exists(TEST_FILE_PATH):
        print(f"❌ FILE NOT FOUND: {TEST_FILE_PATH}")
        return

    try:
        with open(TEST_FILE_PATH, "rb") as f:
            s3.upload_fileobj(f, BUCKET_NAME, TEST_ID)
        print(f"✅ UPLOADED: {TEST_ID} to S3")
    except Exception as e:
        print(f"❌ UPLOAD FAILED: {e}")
        return

    # 2. Pipeline Polling
    stages = [
            ("OCR", "Analysis_OCR", "ocr_worker"), 
            ("Translation (en)", "Analysis_Translations", "translate_worker"),
            ("Summary", "Analysis_Summaries", "summary_worker")
        ]

    for stage_label, table_name, lambda_name in stages:
        print(f"\n⏳ Waiting for {stage_label}...")
        found = False
        table = db.Table(table_name)

        for attempt in range(15): 
            time.sleep(2)
            
            if table_name == "Analysis_Translations":
                response = table.query(KeyConditionExpression=Key('feedback_id').eq(TEST_ID))
                items = response.get('Items', [])
                data = next((i for i in items if i.get('language') == 'en'), None)
            else:
                response = table.get_item(Key={'feedback_id': TEST_ID})
                data = response.get('Item')

            if data:
                print(f"✅ {stage_label} FOUND!")
                found = True
                break
        
        if not found:
            print(f"❌ TIMEOUT: {stage_label} failed to appear.")
            get_latest_logs(lambda_name) 
            return

    print("\n" + "="*60)
    print("🎊 SUCCESS: Full Pipeline Verified Programmatically!")


def update_lambda_code(function_name, file_path, env_vars=None):
    import boto3, zipfile, io
    lmb = boto3.client('lambda', region_name='us-east-1')
    
    # 1. Package the code
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        # Use the base name of the file so it stays 'aws_handler.py'
        z.write(file_path, 'aws_handler.py')
    buf.seek(0)
    
    print(f"🆙 UPDATING AWS LAMBDA CODE FOR: {function_name}...")
    
    # 2. Push the code
    lmb.update_function_code(FunctionName=function_name, ZipFile=buf.read())
    
    # 3. If we have environment variables (like our API Key), push them too
    if env_vars:
        print(f"🔑 Updating environment variables for {function_name}...")
        # Wait for the code update to finish before updating config
        waiter = lmb.get_waiter('function_updated_v2')
        waiter.wait(FunctionName=function_name)
        
        lmb.update_function_configuration(
            FunctionName=function_name,
            Environment={'Variables': env_vars}
        )
    
    print(f"✅ DEPLOYED: {function_name} is ready.")


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv() 

    # Get key from your .env file
    mistral_key = os.getenv("MISTRAL_API_KEY")

    # Update SummaryWorker with BOTH code and the API key
    # Change "summary_worker" to the full ARN to force AWS to find it
    update_lambda_code(
        "arn:aws:lambda:us-east-1:347363495084:function:summary_worker", 
        "lambda/summary_worker/aws_handler.py", 
        env_vars={"MISTRAL_API_KEY": mistral_key}
    )
    run_full_test()