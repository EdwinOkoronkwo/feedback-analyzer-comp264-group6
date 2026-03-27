import boto3

db = boto3.resource('dynamodb', region_name='us-east-1')
table = db.Table('Analysis_Translations')

# Scan all existing translations
items = table.scan()['Items']

print(f"🎙️ Poking {len(items)} translations to generate audio...")

for item in items:
    table.update_item(
        Key={
            'feedback_id': item['feedback_id'],
            'language': item['language']
        },
        UpdateExpression="SET retrigger_time = :t",
        ExpressionAttributeValues={':t': str(boto3.resource('dynamodb').meta.client.meta.region_name)} # Just a dummy value
    )
    print(f"✅ Triggered speech for: {item['feedback_id']} ({item['language']})")

print("\n⏳ Give it 10 seconds, then check S3!")