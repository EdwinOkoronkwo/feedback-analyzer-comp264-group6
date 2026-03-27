import boto3
from botocore.exceptions import ClientError

def initialize_permanent_db():
    # Connect to the persistent local instance
    db = boto3.resource('dynamodb', endpoint_url='http://localhost:8000', region_name='us-east-1')
    
    # We define the three tables required by your models
    table_configs = [
        {"name": "Users", "key": "username"},
        {"name": "Metadata", "key": "feedback_id"},
        {"name": "Summaries", "key": "feedback_id"}
    ]

    for config in table_configs:
        try:
            db.create_table(
                TableName=config["name"],
                KeySchema=[{"AttributeName": config["key"], "KeyType": "HASH"}],
                AttributeDefinitions=[{"AttributeName": config["key"], "AttributeType": "S"}],
                ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
            )
            print(f"✅ Permanent Table Created: {config['name']}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                print(f"ℹ️ Table '{config['name']}' already exists on disk.")
            else:
                print(f"❌ Error: {e}")

if __name__ == "__main__":
    initialize_permanent_db()