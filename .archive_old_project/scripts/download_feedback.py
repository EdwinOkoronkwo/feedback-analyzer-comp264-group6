import boto3
import json
from decimal import Decimal

# Helper to handle DynamoDB Decimals for JSON export
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def download_all_feedback(table_name="FeedbackData", output_file="feedback_backup.json"):
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table(table_name)
    
    print(f"🚀 Starting download from table: {table_name}...")
    
    items = []
    scan_kwargs = {}
    done = False
    
    try:
        while not done:
            response = table.scan(**scan_kwargs)
            items.extend(response.get('Items', []))
            
            # Check if there is more data to fetch (Pagination)
            next_key = response.get('LastEvaluatedKey')
            if not next_key:
                done = True
            else:
                scan_kwargs['ExclusiveStartKey'] = next_key

        # Save to local file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(items, f, cls=DecimalEncoder, indent=4)
            
        print(f"✅ Success! {len(items)} records downloaded to {output_file}")
        
    except Exception as e:
        print(f"❌ Error downloading data: {str(e)}")

if __name__ == "__main__":
    download_all_feedback()