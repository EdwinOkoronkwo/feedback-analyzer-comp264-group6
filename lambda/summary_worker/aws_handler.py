import boto3
import json
import os
import urllib3

# Initialize Clients
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
lambda_client = boto3.client('lambda', region_name='us-east-1')

def get_mistral_summary(text, api_key):
    if not api_key:
        return "Error: Mistral API Key is missing"

    m_url = "https://api.mistral.ai/v1/chat/completions"
    http = urllib3.PoolManager()
    
    prompt = f"Summarize this feedback in exactly 10 words: '{text}'"
    payload = {
        "model": "mistral-medium-latest",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 50
    }
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    try:
        encoded_data = json.dumps(payload).encode('utf-8')
        res = http.request('POST', m_url, body=encoded_data, headers=headers, timeout=10.0)
        
        if res.status != 200:
            return f"Error: Mistral API returned {res.status}"
            
        result = json.loads(res.data.decode('utf-8'))
        return result['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"❌ MISTRAL ERROR: {str(e)}")
        return f"Summary unavailable: {str(e)[:20]}"

        
def lambda_handler(event, context):
    fid = event.get('feedback_id')
    # The Master Worker or Analysis Worker passes the text here
    text_to_process = event.get('text') or event.get('translated_text')
    
    # 1. Get the Summary from Mistral
    summary = get_mistral_summary(text_to_process, os.environ.get('MISTRAL_API_KEY'))

    # 2. 🏁 The Final Update
    # We map 'status' to '#stat' because 'status' is a reserved keyword in DynamoDB
    try:
        table = dynamodb.Table('Analysis_Summaries')
        table.update_item(
            Key={'feedback_id': fid},
            UpdateExpression="SET summary = :s, #stat = :c, translated_text = :t",
            ExpressionAttributeValues={
                ':s': summary, 
                ':c': 'COMPLETED',
                ':t': text_to_process # Ensures "Translated Text" isn't N/A in the UI
            },
            ExpressionAttributeNames={'#stat': 'status'}
        )
        print(f"✅ Finalized record for {fid}")
    except Exception as e:
        print(f"❌ DB Update Failed: {e}")
    # 4. RELAY: Trigger Speech Worker
    # Send the 'summary' to Polly so it reads the AI summary, not the raw text
    lambda_client.invoke(
        FunctionName='speech_worker',
        InvocationType='Event',
        Payload=json.dumps({
            "feedback_id": fid, 
            "text": summary, # Have Polly read the summary!
            "language": event.get('language', 'en')
        }).encode('utf-8')
    )

    return {"status": "success", "summary": summary}