import datetime
import json
import os
import requests
from scripts.db_config import get_dynamodb_resource

# Initialize Local DynamoDB
dynamodb = get_dynamodb_resource()

# 🎯 FIX 1: Align with your actual local table name
# We'll use 'Summaries' as the master table for finalized data
table = dynamodb.Table('Summaries')

def lambda_handler(event, context):
    """
    Local Analysis Worker: 
    Finalizes the record by generating Summary, Sentiment, and Translation in one go.
    """
    mistral_key = os.environ.get('MISTRAL_API_KEY')
    dashboard_dir = "static/live-data"
    if not os.path.exists(dashboard_dir):
        os.makedirs(dashboard_dir)

    # 1. Handle Input
    body = event.get('body', {})
    fid = body.get('feedback_id', 'unknown')
    raw_text = body.get('text', '')

    if not raw_text:
        return {"status": "error", "message": "No text provided", "summary": "N/A"}

    try:
        print(f"📈 Finalizing Analysis for {fid}...")

        # 2. Combined AI Analysis
        m_url = "https://api.mistral.ai/v1/chat/completions"
        prompt = (
            f"Analyze this feedback: '{raw_text}'. "
            "1. Translate it to English. "
            "2. Determine sentiment (POSITIVE/NEGATIVE/NEUTRAL). "
            "3. Summarize in 10 words. "
            "Return a JSON object with keys: 'translated', 'sentiment', 'summary'."
        )
        
        m_body = {
            "model": "mistral-medium-latest",
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"}
        }
        
        res = requests.post(m_url, 
                            headers={'Authorization': f'Bearer {mistral_key}'}, 
                            json=m_body, timeout=15)
        res.raise_for_status()
        
        # 🎯 FIX 2: Safely parse the AI content
        ai_response = res.json()
        analysis = json.loads(ai_response['choices'][0]['message']['content'])

        # 3. Create Payload
        payload = {
            "feedback_id": fid,
            "sentiment": analysis.get('sentiment', 'NEUTRAL').upper(),
            "summary": analysis.get('summary', 'No summary available'),
            "translated_text": analysis.get('translated', raw_text),
            "timestamp": datetime.datetime.now().isoformat(),
            "status": "COMPLETED"
        }

        # 4. Save Locally (JSON Dashboard file)
        file_path = os.path.join(dashboard_dir, f"{fid}.json")
        with open(file_path, "w") as f:
            json.dump(payload, f)

        # 5. Update Local DynamoDB ('Summaries' table)
        # 🎯 FIX 3: Use the aligned table name to stop ResourceNotFoundException
        table.put_item(Item=payload)

        print(f"✅ Analysis Saved for {fid}")

        # 🎯 FIX 4: RETURN THE DICT
        # This prevents the 'str has no attribute get' error in Flask
        return {
            "status": "success",
            "feedback_id": fid,
            "summary": payload["summary"],
            "sentiment": payload["sentiment"],
            "translated_text": payload["translated_text"]
        }

    except Exception as e:
        print(f"❌ Analysis Error for {fid}: {str(e)}")
        # Return a safe dictionary even on failure
        return {
            "status": "error", 
            "message": str(e), 
            "summary": "Error during analysis", 
            "sentiment": "NEUTRAL"
        }