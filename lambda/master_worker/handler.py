import time
from scripts.db_config import get_dynamodb_resource

dynamodb = get_dynamodb_resource()

def lambda_handler(event, context):
    body = event.get('body', {})
    fid = body.get('feedback_id')
    user_id = body.get('user_id', 'anonymous')
    
    print(f"🚀 Orchestrating Final Assembly for: {fid}")

    # 1. Trigger the specialized workers (Fan-out)
    # Note: In a real AWS environment, these would be async SNS/SQS calls
    # For your local VMware setup, direct imports are fine.
    from ocr_worker.handler import lambda_handler as ocr_handler
    from label_worker.handler import lambda_handler as label_handler
    from summary_worker.handler import lambda_handler as summary_handler
    
    ocr_handler(event, context)
    label_handler(event, context)
    summary_result = summary_handler(event, context) # This gives us the Mistral output

    # 2. THE AGGREGATION (Single Responsibility: "The Assembler")
    # Fetch the "scratchpad" data created by the workers above
    try:
        # Give a millisecond for local DB writes to settle
        time.sleep(0.5) 
        
        ocr_item = dynamodb.Table('Analysis_OCR').get_item(Key={'feedback_id': fid}).get('Item', {})
        label_item = dynamodb.Table('Analysis_Labels').get_item(Key={'feedback_id': fid}).get('Item', {})
        
        # 3. Create the "Rich Document" (The NoSQL Way)
        final_document = {
            'feedback_id': fid,
            'user_id': user_id,
            'status': 'COMPLETED',
            'summary': summary_result.get('summary'),
            'sentiment': summary_result.get('sentiment'),
            'ocr_details': ocr_item,
            'labels': label_item.get('labels', []),
            'processed_at': str(time.time())
        }

        # 4. Save to the Final Dashboard Table
        dynamodb.Table('Analysis_Summary').put_item(Item=final_document)
        
        return {"status": "SUCCESS", "id": fid}

    except Exception as e:
        print(f"❌ Orchestration Error: {e}")
        return {"status": "FAILED", "error": str(e)}