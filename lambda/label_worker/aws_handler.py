import boto3
import json

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

def lambda_handler(event, context):
    # 🎯 FIX: Direct access from Step Function payload
    fid = event.get('feedback_id')
    full_text = event.get('text')
    
    try:
        # Simple Keyword Labeling
        text_lower = full_text.lower() if full_text else ""
        if any(word in text_lower for word in ['séries', 'télé', 'star', 'house']):
            label = "ENTERTAINMENT"
        else:
            label = "GENERAL_FEEDBACK"
        
        # Update DynamoDB
        table = dynamodb.Table('Analysis_Summaries')
        table.update_item(
            Key={'feedback_id': fid},
            UpdateExpression="SET #s = :stat, label = :lbl",
            ExpressionAttributeNames={'#s': 'status'},
            ExpressionAttributeValues={':stat': 'COMPLETED', ':lbl': label}
        )

        return {
            "feedback_id": fid,
            "sentiment": event.get('sentiment'),
            "summary": event.get('summary'),
            "label": label,
            "status": "FINAL_SUCCESS"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}