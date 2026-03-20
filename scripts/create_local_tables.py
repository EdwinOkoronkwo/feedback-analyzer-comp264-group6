import boto3

# Connect to Local DynamoDB
db = boto3.resource('dynamodb', endpoint_url='http://localhost:8000', region_name='us-east-1')

def create_local_tables():
    # 1. Create Users Table
    try:
        db.create_table(
            TableName='Users',
            KeySchema=[{'AttributeName': 'username', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'username', 'AttributeType': 'S'}],
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        print("✅ 'Users' table created.")
    except Exception as e: print(f"⚠️ Users table might already exist: {e}")

    # 2. Create Feedback Table
    try:
        db.create_table(
            TableName='Feedback_Master',
            KeySchema=[{'AttributeName': 'feedback_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'feedback_id', 'AttributeType': 'S'}],
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        print("✅ 'Feedback_Master' table created.")
    except Exception as e: print(f"⚠️ Feedback_Master table might already exist: {e}")

if __name__ == "__main__":
    create_local_tables()