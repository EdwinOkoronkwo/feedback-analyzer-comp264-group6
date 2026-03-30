import boto3
import json
import os
import urllib3

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
lambda_client = boto3.client('lambda', region_name='us-east-1')

def get_mistral_summary(text, api_key):
    if not api_key: return "Error: API Key Missing"
    
    m_url = "https://api.mistral.ai/v1/chat/completions"
    http = urllib3.PoolManager()
    
    # Updated Prompt: Better for Tobacco Industry documents
    prompt = (
        "You are an AI research assistant. Summarize the following document "
        "in one concise sentence (max 20 words), focusing on the main topic and intent: "
        f"'{text}'"
    )
    
    payload = {
        "model": "mistral-medium-latest",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3 # Lower temperature for more factual summaries
    }
    
    headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}

    try:
        encoded_data = json.dumps(payload).encode('utf-8')
        res = http.request('POST', m_url, body=encoded_data, headers=headers, timeout=12.0)
        
        if res.status != 200:
            return f"Summary error: Status {res.status}"
            
        result = json.loads(res.data.decode('utf-8'))
        return result['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"Mistral timeout: {str(e)[:25]}"

def lambda_handler(event, context):
    fid = event.get('feedback_id')
    # Support both 'text' (Standard) and 'translated_text' (from Analysis worker)
    text_to_process = event.get('text') or event.get('translated_text', '')
    
    if not text_to_process:
        print(f"⚠️ No text to summarize for {fid}")
        return {"status": "error"}

    # 1. Generate Summary
    summary = get_mistral_summary(text_to_process, os.environ.get('MISTRAL_API_KEY'))

    # 2. Update DynamoDB (Using update_item to be non-destructive)
    try:
        table = dynamodb.Table('Analysis_Summaries')
        table.update_item(
            Key={'feedback_id': fid},
            UpdateExpression="SET summary = :s, #stat = :c, master = :m",
            ExpressionAttributeValues={
                ':s': summary, 
                ':c': 'SUMMARIZED', # We keep it 'SUMMARIZED' until Polly is done
                ':m': "🤖 Mistral analysis complete. Generating voice..."
            },
            ExpressionAttributeNames={'#stat': 'status'}
        )
    except Exception as e:
        print(f"❌ DB Error: {e}")

    # 3. 🎙️ THE FINAL RELAY: Trigger Speech Worker
    try:
        lambda_client.invoke(
            FunctionName='speech_worker',
            InvocationType='Event',
            Payload=json.dumps({
                "feedback_id": fid, 
                "text": summary, 
                "language": event.get('language', 'en')
            }).encode('utf-8')
        )
        print(f"✅ [SUMMARIZER] Handed off {fid} to Speech Worker.")
    except Exception as e:
        print(f"❌ Speech Trigger Failed: {e}")

    return {"status": "success", "summary": summary}