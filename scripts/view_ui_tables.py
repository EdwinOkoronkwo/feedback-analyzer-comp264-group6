import boto3
from boto3.dynamodb.conditions import Key

db = boto3.resource('dynamodb', endpoint_url='http://localhost:8000', region_name='us-east-1')
table = db.Table('FeedbackData')

# 1. See what is actually inside the table
response = table.scan()
items = response.get('Items', [])

if not items:
    print("❌ The table 'FeedbackData' is still EMPTY. The save operation failed.")
else:
    print(f"✅ Found {len(items)} records!")
    for item in items:
        print(f"ID: {item.get('feedback_id')} | User: {item.get('username')} | Status: {item.get('status')}")