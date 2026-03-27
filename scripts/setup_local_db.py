import boto3
import bcrypt  # <--- ADD THIS LINE HERE
from botocore.exceptions import ClientError
import os

# Configuration for VMware Local Environment
LOCAL_ENDPOINT = "http://localhost:8000"
REGION = "us-east-1"
# scripts/setup_local_db.py
TABLES = {
    "Analysis_Summaries": "feedback_id",
    "Feedback_Users": "username",
    "Feedback_Metadata": "feedback_id"  # <--- ADD THIS LINE
}

def get_local_client():
    return boto3.client(
        'dynamodb', 
        endpoint_url=LOCAL_ENDPOINT, 
        region_name=REGION
    )

def setup_tables():
    db = get_local_client()
    print(f"🚀 Initializing Local DynamoDB at {LOCAL_ENDPOINT}...")

    for table_name, partition_key in TABLES.items():
        try:
            print(f"📡 Creating table: {table_name}...")
            db.create_table(
                TableName=table_name,
                KeySchema=[{'AttributeName': partition_key, 'KeyType': 'HASH'}],
                AttributeDefinitions=[{'AttributeName': partition_key, 'AttributeType': 'S'}],
                ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
            )
            # Wait for table to be ready
            waiter = db.get_waiter('table_exists')
            waiter.wait(TableName=table_name)
            print(f"✅ {table_name} is READY.")
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                print(f"ℹ️ {table_name} already exists. Skipping.")
            else:
                print(f"❌ Error creating {table_name}: {e}")

def seed_admin():
    db = get_local_client()
    print("👤 Seeding Local Admin User...")
    try:
        db.put_item(
            TableName="Feedback_Users",
            Item={
                'username': {'S': 'admin'},
                'role': {'S': 'admin'},
                'password_hash': {'S': 'SECRET_HASH'} # Replace with actual hash later
            }
        )
        print("✅ Admin user seeded successfully.")
    except Exception as e:
        print(f"⚠️ Seeding failed: {e}")

def seed_admin():
    db = get_local_client()
    
    # 1. Generate a real bcrypt hash for 'password123'
    # Use a 'salt' so the UserService can verify it correctly
    plain_password = "password123"
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(plain_password.encode('utf-8'), salt).decode('utf-8')
    
    print(f"👤 Seeding Local Admin User with password: {plain_password}")
    try:
        db.put_item(
            TableName="Feedback_Users",
            Item={
                'username': {'S': 'admin'},
                'role': {'S': 'admin'},
                'password_hash': {'S': hashed_password} 
            }
        )
        print("✅ Admin user seeded with a valid Bcrypt Salt.")
    except Exception as e:
        print(f"⚠️ Seeding failed: {e}")

if __name__ == "__main__":
    setup_tables()
    seed_admin()
    print("\n✨ Local Database is fully configured for VMware Mode.")