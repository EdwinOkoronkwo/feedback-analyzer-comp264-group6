#import random
import random
import uuid
import json
import boto3
from datetime import datetime

# AWS Clients
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

# Configuration - CHECK THESE MATCH YOUR AWS SETUP
BUCKET = "comp264-edwin-1772030214"
TABLE_SUMMARY = "Analysis_Summaries"
TABLE_TRANSLATE = "Analysis_Translations"

def seed_live_analytics(count=10):
    print(f"🚀 Seeding {count} records to DynamoDB and S3...")
    
    templates = [
        {"text": "Amazing experience!", "sent": "POSITIVE", "summ": "User had a great time."},
        {"text": "The food was cold.", "sent": "NEGATIVE", "summ": "Service issue: cold food."},
        {"text": "El servicio fue increíble.", "sent": "POSITIVE", "summ": "Excellent service feedback."},
    ]

    for i in range(count):
        template = random.choice(templates)
        feedback_id = f"seed_{uuid.uuid4().hex[:8]}.txt"
        ts = datetime.utcnow().isoformat()

        # 1. Seed DynamoDB Analysis_Summaries (For the Pipeline UI)
        summary_table = dynamodb.Table(TABLE_SUMMARY)
        summary_table.put_item(Item={
            'feedback_id': feedback_id,
            'sentiment': template['sent'],
            'summary_text': template['summ'],
            'timestamp': ts
        })

        # 2. Seed DynamoDB Analysis_Translations (For the Pipeline UI)
        translate_table = dynamodb.Table(TABLE_TRANSLATE)
        translate_table.put_item(Item={
            'feedback_id': feedback_id,
            'translated_text': f"Translated: {template['text']}",
            'language': 'es'
        })

        # 3. Seed S3 live-data folder (FOR THE ANALYTICS TOTALS)
        # This is what Athena looks at!
        analytics_payload = {
            "item": {
                "feedback_id": feedback_id,
                "sentiment": {"s": template['sent']},
                "summary": template['summ'],
                "timestamp": ts
            }
        }
        
        s3.put_object(
            Bucket=BUCKET,
            Key=f"live-data/{feedback_id}.json",
            Body=json.dumps(analytics_payload)
        )

    print(f"✅ Successfully seeded {count} records. Your dashboard should now be LIVE.")

if __name__ == "__main__":
    seed_live_analytics(15)