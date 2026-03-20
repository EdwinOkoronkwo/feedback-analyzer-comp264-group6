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
    # 1. Handle Input (Allow for 'text' or 'translated_text' or 'ocr_text')
    fid = event.get('feedback_id')
    # If it's direct text, it might just be in 'text'
    text_to_process = event.get('translated_text') or event.get('text') or event.get('ocr_text')
    mistral_key = os.environ.get('MISTRAL_API_KEY')

    if not text_to_process or text_to_process == "N/A":
        print(f"⚠️ No text found for {fid}")
        return {"status": "error", "message": "No text to process"}

    print(f"🤖 Summarizer Worker: Requesting Mistral summary for {fid}")

    # 2. Get Mistral Summary
    summary = get_mistral_summary(text_to_process, mistral_key)

    # 3. 🎯 THE CRITICAL FIX: Update DynamoDB with BOTH Summary AND Status
    # This 'status' change is what tells the UI to stop polling!
    dynamodb.Table('Analysis_Summaries').update_item(
        Key={'feedback_id': fid},
        UpdateExpression="SET summary = :s, #stat = :c, translated_text = :t",
        ExpressionAttributeValues={
            ':s': summary, 
            ':c': 'COMPLETED',
            ':t': text_to_process # Save it here so 'Translated Text' isn't N/A in the UI
        },
        ExpressionAttributeNames={'#stat': 'status'}
    )

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