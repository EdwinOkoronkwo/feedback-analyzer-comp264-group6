from dotenv import load_dotenv
import boto3
import time

load_dotenv()

def create_table(dynamodb, table_name, key_name):
    """Generic function to create a DynamoDB table if it doesn't exist."""
    try:
        print(f"🚀 Creating table '{table_name}'...")
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[{'AttributeName': key_name, 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': key_name, 'AttributeType': 'S'}],
            # Using Provisioned for the project is fine, or BillingMode='PAY_PER_REQUEST'
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        
        print(f"⏳ Waiting for {table_name} to become ACTIVE...")
        table.meta.client.get_waiter('table_exists').wait(TableName=table_name)
        print(f"✅ Table {table_name} is now ACTIVE.")
        
    except Exception as e:
        if "ResourceInUseException" in str(e):
            print(f"ℹ️ Table '{table_name}' already exists.")
        else:
            print(f"❌ Error creating {table_name}: {e}")

def run_setup():
    # Ensure you have your AWS credentials configured in .env or ~/.aws/credentials
    dynamodb = boto3.resource('dynamodb')
    
    # 1. Create Feedback Table (Partition Key: id)
    create_table(dynamodb, "FeedbackData", "id")
    
    # 2. Create Users Table (Partition Key: username)
    # Note: We use 'username' as the HASH key for fast login lookups
    create_table(dynamodb, "Users", "username")

if __name__ == "__main__":
    run_setup()