import boto3
import time

def reset_local_environment():
    db = boto3.client('dynamodb', endpoint_url='http://localhost:8000', region_name='us-east-1')
    
    # THE MASTER SCHEMA (The only tables allowed to exist)
    # Table Name : Primary Key
    master_schema = {
        "Users": "username",
        "Analysis_Metadata": "feedback_id",  # Replaces 'Feedback', 'FeedbackData', etc.
        "Analysis_Summary": "feedback_id"    # The source of truth for the UI
    }

    print("🛑 SHUTTING DOWN LEGACY DATA...")
    
    # 1. Identify all existing tables
    existing_tables = db.list_tables()['TableNames']
    
    # 2. Wipe the slate clean
    for table in existing_tables:
        print(f"🗑️  Deleting {table}...")
        try:
            db.delete_table(TableName=table)
        except Exception as e:
            print(f"⚠️ Could not delete {table}: {e}")

    # 3. Wait for AWS Local to process deletions
    print("⏳ Waiting for total purge...")
    time.sleep(2)

    # 4. Rebuild the Strict Environment
    print("\n🏗️  BUILDING STRUCTURED TABLES...")
    for table_name, pk in master_schema.items():
        try:
            db.create_table(
                TableName=table_name,
                KeySchema=[{'AttributeName': pk, 'KeyType': 'HASH'}],
                AttributeDefinitions=[{'AttributeName': pk, 'AttributeType': 'S'}],
                ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
            )
            print(f"✅ Created {table_name} (PK: {pk})")
        except Exception as e:
            print(f"❌ Error creating {table_name}: {e}")

    print("\n✨ LOCAL DB IS CLEAN. RUNNING ON MASTER SCHEMA ONLY.")

if __name__ == "__main__":
    reset_local_environment()