import boto3
from decimal import Decimal

# Initialize DynamoDB Resource
db = boto3.resource('dynamodb', endpoint_url='http://localhost:8000', region_name='us-east-1')
table = db.Table('Analysis_Summary')

def migrate_feedback_data():
    print("🔍 Scanning for legacy records in Analysis_Summary...")
    response = table.scan()
    items = response.get('Items', [])
    
    if not items:
        print("ℹ️ No records found to migrate.")
        return

    count = 0
    for item in items:
        changed = False
        
        # 1. Rename 'summary_text' to 'text' (The positional argument fix)
        if 'summary_text' in item and 'text' not in item:
            item['text'] = item.pop('summary_text')
            changed = True
            
        # 2. Ensure 'user_id' exists (The auth filter fix)
        if 'username' in item and 'user_id' not in item:
            item['user_id'] = item.pop('username')
            changed = True

        # 3. Ensure 'id' exists if 'feedback_id' is the only one
        if 'feedback_id' in item and 'id' not in item:
            item['id'] = item['feedback_id'] # Keep both for safety
            changed = True

        if changed:
            table.put_item(Item=item)
            count += 1
            print(f"✅ Migrated Record ID: {item.get('id') or item.get('feedback_id')}")

    print(f"\n🚀 Migration Complete! {count} records updated.")

if __name__ == "__main__":
    migrate_feedback_data()