import boto3
import json

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

def lambda_handler(event, context):
    fid = event.get('feedback_id')
    full_text = event.get('text')
    sentiment = event.get('sentiment')

    try:
        print(f"📝 Summary Worker: Processing {fid}")

        # Basic Summarization (Example: First 50 chars + "...")
        # In a real app, you might use Bedrock or a NLP model here.
        summary_text = (full_text[:47] + '...') if len(full_text) > 50 else full_text
        
        # Update DynamoDB (Audit Trail)
        table = dynamodb.Table('Analysis_Summaries')
        # Inside summary_worker.py
        table.update_item(
            Key={'feedback_id': fid},
            UpdateExpression="SET #s = :stat, summary = :summ",
            ExpressionAttributeNames={'#s': 'status'},
            ExpressionAttributeValues={
                ':stat': 'COMPLETED',  # <--- Standardized
                ':summ': summary_text
            }
        )

        # 🚩 THE RETURN (Passed to next step)
        # 🚩 THE RETURN (Passed to next step)
        return {
            **event, # 👈 This preserves 'bucket', 'key', and anything else from earlier steps
            "summary": summary_text,
            "status": "SUMMARY_SUCCESS"
        }
    except Exception as e:
        print(f"❌ Summary Error: {str(e)}")
        raise e