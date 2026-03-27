import boto3

def clear_feedback_table(table_name="FeedbackData"):
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table(table_name)
    
    print(f"⚠️ Preparing to clear all records from {table_name}...")
    
    # 1. Scan to get all keys
    response = table.scan(ProjectionExpression="id")
    items = response.get('Items', [])
    
    if not items:
        print("✅ Table is already empty.")
        return

    # 2. Batch delete (more efficient than individual deletes)
    with table.batch_writer() as batch:
        for item in items:
            batch.delete_item(Key={'id': item['id']})
            
    print(f"🗑️ Deleted {len(items)} records. Your table is now clean!")

if __name__ == "__main__":
    confirm = input("This will delete ALL feedback data. Type 'yes' to proceed: ")
    if confirm.lower() == 'yes':
        clear_feedback_table()
    else:
        print("Aborted.")