import boto3
import pandas as pd
from datetime import datetime, timedelta

def live_trace_test():
    REGION = "us-east-1"
    db = boto3.resource('dynamodb', region_name=REGION)
    s3 = boto3.client('s3', region_name=REGION)
    
    # Tables to check
    tables = ['Analysis_Translations', 'Analysis_Summaries']
    
    print(f"🕵️ Scanning for recent activity (Last 2 minutes)...")
    
    # 1. Check DynamoDB Tables (UI Pipeline)
    for table_name in tables:
        print(f"\n--- Checking {table_name} ---")
        table = db.Table(table_name)
        response = table.scan()
        items = response.get('Items', [])
        
        if items:
            df = pd.DataFrame(items)
            # Look for non-seed data (UUIDs)
            real_data = df[~df['feedback_id'].str.contains('seed_', na=False)]
            if not real_data.empty:
                print(f"✅ Found {len(real_data)} new items in {table_name}!")
                print(real_data.tail(2).to_string(index=False))
            else:
                print("⚠️ Only seed data found. UI-to-Table hook is MISSING.")
        else:
            print("📭 Table is empty.")

    # 2. Check S3 (Analytics Dashboard)
    print(f"\n--- Checking S3 live-data/ ---")
    bucket = "comp264-edwin-1772030214" # Update to your bucket name
    try:
        objs = s3.list_objects_v2(Bucket=bucket, Prefix='live-data/')
        if 'Contents' in objs:
            # Sort by last modified
            latest = sorted(objs['Contents'], key=lambda x: x['LastModified'], reverse=True)[0]
            print(f"✅ Latest S3 File: {latest['Key']} (Uploaded: {latest['LastModified']})")
        else:
            print("❌ No files found in S3 live-data/. Dashboard hook is MISSING.")
    except Exception as e:
        print(f"❌ S3 Error: {e}")

if __name__ == "__main__":
    live_trace_test()