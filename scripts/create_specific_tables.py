import boto3

def setup_specific_tables():
    dynamodb = boto3.client('dynamodb', region_name='us-east-1')
    
    # Define our micro-tables
    table_configs = [
        "Analysis_Labels",
        "Analysis_OCR",
        "Analysis_Speech"
    ]

    for table_name in table_configs:
        try:
            print(f"⏳ Creating {table_name}...")
            dynamodb.create_table(
                TableName=table_name,
                KeySchema=[{'AttributeName': 'feedback_id', 'KeyType': 'HASH'}],
                AttributeDefinitions=[{'AttributeName': 'feedback_id', 'AttributeType': 'S'}],
                ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
            )
            print(f"✅ {table_name} created successfully.")
        except dynamodb.exceptions.ResourceInUseException:
            print(f"ℹ️ {table_name} already exists.")
        except Exception as e:
            print(f"❌ Error creating {table_name}: {e}")

if __name__ == "__main__":
    setup_specific_tables()