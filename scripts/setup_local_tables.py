import boto3
import os

def setup_local_tables():
    # Toggle this to False if you ever go back to the cloud
    USE_LOCAL = True
    
    endpoint = "http://localhost:8000" if USE_LOCAL else None
    
    dynamodb = boto3.client(
        'dynamodb', 
        region_name='us-east-1', 
        endpoint_url=endpoint
    )
    
    # Define tables and their specific Primary Keys
    # Users needs 'username', everything else needs 'feedback_id'
    table_configs = {
        "Users": "username",
        "Feedback": "feedback_id",
        "Feedbacks": "feedback_id",      # Added
        "Feedback_Master": "feedback_id",
        "Analysis_Labels": "feedback_id",
        "Analysis_OCR": "feedback_id",
        "Analysis_Speech": "feedback_id",
        "Analysis_Summary": "feedback_id",
        "Analysis_Summaries": "feedback_id",
        "Analysis_Translations": "feedback_id",
        "Analysis_Results": "feedback_id" # Added
    }
    for table_name, pk_name in table_configs.items():
        try:
            print(f"⏳ Creating {table_name} (Primary Key: {pk_name})...")
            dynamodb.create_table(
                TableName=table_name,
                KeySchema=[{'AttributeName': pk_name, 'KeyType': 'HASH'}],
                AttributeDefinitions=[{'AttributeName': pk_name, 'AttributeType': 'S'}],
                ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
            )
            print(f"✅ {table_name} created successfully.")
        except dynamodb.exceptions.ResourceInUseException:
            print(f"ℹ️ {table_name} already exists.")
        except Exception as e:
            print(f"❌ Error creating {table_name}: {e}")

if __name__ == "__main__":
    setup_local_tables()