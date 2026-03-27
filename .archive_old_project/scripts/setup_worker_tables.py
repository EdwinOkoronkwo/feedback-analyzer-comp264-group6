import boto3

db = boto3.client('dynamodb', endpoint_url='http://localhost:8000', region_name='us-east-1')

# This list is derived EXACTLY from your grep results of the lambda/ folder
worker_tables = [
    "FeedbackData",
    "FeedbackMedia",
    "Feedback_Master",
    "Analysis_Labels",
    "Analysis_Translations",
    "Analysis_Speech",
    "Analysis_Summary",   # Singular
    "Analysis_Summaries",  # Plural (for the UI)
    "Analysis_OCR"
]

for t in worker_tables:
    try:
        db.create_table(
            TableName=t,
            KeySchema=[{'AttributeName': 'feedback_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'feedback_id', 'AttributeType': 'S'}],
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        print(f"✅ Created {t}")
    except Exception:
        print(f"ℹ️ {t} already exists")