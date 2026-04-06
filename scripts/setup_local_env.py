import boto3
import bcrypt
from botocore.exceptions import ClientError

# --- CONFIGURATION (Synced with your .db file and AWS names) ---
LOCAL_URL = "http://localhost:8000"
REGION = "us-east-1"
DUMMY_KEY = "AKIAEXAMPLE123456789"
DUMMY_SECRET = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

# These match your 'aws dynamodb list-tables' output
TABLES = {
    "Metadata": "feedback_id",
    "Summaries": "feedback_id",
    "Users": "username"
}

# Credentials to seed
ADMIN_USER = "admin"
ADMIN_PASS = "password123"

# Connect to the local Java engine
dynamodb = boto3.client(
    'dynamodb',
    endpoint_url=LOCAL_URL,
    region_name=REGION,
    aws_access_key_id=DUMMY_KEY,
    aws_secret_access_key=DUMMY_SECRET
)

def setup_local():
    print("🏗️  Initializing Local VMware Infrastructure...")

    # 1. Create Tables
    for table_name, pk in TABLES.items():
        try:
            dynamodb.create_table(
                TableName=table_name,
                KeySchema=[{'AttributeName': pk, 'KeyType': 'HASH'}],
                AttributeDefinitions=[{'AttributeName': pk, 'AttributeType': 'S'}],
                ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
            )
            print(f"✅ Table '{table_name}' Created.")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                print(f"ℹ️  Table '{table_name}' already exists.")
            else:
                print(f"❌ Error creating {table_name}: {e}")

    # 2. Seed Admin User (Equivalent to your AWS User setup)
    print(f"👤 Seeding default user: {ADMIN_USER}...")
    
    # Generate hash using standard bcrypt
    hashed_pw = bcrypt.hashpw(ADMIN_PASS.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    try:
        dynamodb.put_item(
            TableName="Users",
            Item={
                'username': {'S': ADMIN_USER},
                'password_hash': {'S': hashed_pw},
                'role': {'S': 'admin'},
                'created_at': {'S': '2026-04-05T15:00:00'}
            }
        )
        print("✅ Admin user ready.")
    except Exception as e:
        print(f"❌ Failed to seed user: {e}")

    print("\n✨ LOCAL SYSTEM ONLINE. Tables are ready and synced with code.")

if __name__ == "__main__":
    setup_local()