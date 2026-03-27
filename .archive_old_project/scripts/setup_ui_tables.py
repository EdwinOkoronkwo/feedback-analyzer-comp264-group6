import boto3

# Connect to your local DynamoDB
db = boto3.client('dynamodb', endpoint_url='http://localhost:8000', region_name='us-east-1')

# The EXACT names found in your grep search
required_tables = [
    "FeedbackData",           # The main culprit!
    "Analysis_Summaries",    # Plural version
    "Analysis_Translations", # For the pipeline
    "Users"                  # Already exists, but safe to include
]

for t in required_tables:
    try:
        print(f"⏳ Creating {t}...")
        db.create_table(
            TableName=t,
            # Based on your code, these all use feedback_id except Users (which uses username)
            KeySchema=[{'AttributeName': 'username' if t == "Users" else 'feedback_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'username' if t == "Users" else 'feedback_id', 'AttributeType': 'S'}],
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        print(f"✅ {t} created successfully.")
    except Exception as e:
        print(f"ℹ️ {t} status: {e}")