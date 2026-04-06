# import json
# import time
# import os
# import requests
# from scripts.db_config import get_dynamodb_resource

# # --- 🎯 THE PLAN: ALIGN TABLE NAME ---
# # Initializing connection to the local 'Summaries' table
# dynamodb = get_dynamodb_resource()
# table = dynamodb.Table('Summaries') 

# def lambda_handler(event, context):
#     """
#     Hybrid Worker: Local Database + Mistral Medium AI.
#     Saves the final 'Fat Document' to the local Summaries table.
#     """
#     # 1. Configuration
#     api_key = os.environ.get('MISTRAL_API_KEY')
#     body = event.get('body', {})
    
#     # 🆔 THE MASTER ID: This must match the ID sent by the Flask Bridge
#     fid = body.get('feedback_id', 'unknown')
#     user_id = body.get('user_id', 'anonymous')
#     raw_text = body.get('text', '')
#     text_to_analyze = body.get('translated_text') or raw_text

#     if not raw_text:
#         return {"status": "error", "message": "No text provided to worker"}

#     # 2. AI Analysis via Mistral
#     url = "https://api.mistral.ai/v1/chat/completions"
#     headers = {
#         "Content-Type": "application/json",
#         "Authorization": f"Bearer {api_key}"
#     }
    
#     prompt = (
#         f"Analyze this feedback: '{text_to_analyze}'. "
#         "Return a JSON object with two keys: "
#         "'summary' (one short sentence) and 'sentiment' (POSITIVE, NEGATIVE, or NEUTRAL)."
#     )
    
#     payload = {
#         "model": "mistral-medium-latest",
#         "messages": [{"role": "user", "content": prompt}],
#         "response_format": {"type": "json_object"} 
#     }

#     try:
#         # 3. Call AI
#         print(f"🌟 [Worker] Calling Mistral Medium for ID: {fid}...")
#         response = requests.post(url, json=payload, headers=headers, timeout=15)
#         response.raise_for_status()
        
#         ai_data = response.json()
#         raw_content = ai_data['choices'][0]['message']['content'].strip()

#         # 🎯 THE FIX: Remove Markdown backticks if Mistral included them
#         if raw_content.startswith("```"):
#             # Strip ```json at start and ``` at end
#             raw_content = raw_content.split("json")[-1].strip("`").strip()

#         ai_content = json.loads(raw_content)
        
#         summary = ai_content.get('summary', 'No summary generated.')
#         sentiment = ai_content.get('sentiment', 'NEUTRAL').upper()
#         # 4. Save to Local DynamoDB ('Summaries' Table)
#         # 📝 ANCHOR LOG: Look for this in your FLASK terminal
#         print(f"[WORKER] 💾 SAVING -> Table: Summaries | Key: {fid}")

#         table.put_item(Item={
#             'feedback_id': fid,          # PRIMARY KEY
#             'user_id': user_id,
#             'text': raw_text,
#             'translated_text': body.get('translated_text'),
#             'summary': summary,
#             'sentiment': sentiment,
#             'labels': body.get('labels', []),
#             'ocr_details': body.get('ocr_details', {}),
#             'processed_at': str(time.time()),
#             'status': 'COMPLETED'
#         })
        
#         print(f"✅ [Worker] Success: {fid} recorded.")
#         return {
#             "status": "success", 
#             "feedback_id": fid, 
#             "summary": summary, 
#             "sentiment": sentiment
#         }

#     except Exception as e:
#         print(f"❌ [Worker] Error: {str(e)}")
#         return {"status": "error", "message": str(e)}


import json
import time
import os
import requests
from scripts.db_config import get_dynamodb_resource

dynamodb = get_dynamodb_resource()
table = dynamodb.Table('Summaries') 

def lambda_handler(event, context=None):
    # 🎯 Robust extraction of relay data
    body = event.get('body') if 'body' in event else event
    fid = body.get('feedback_id')
    raw_text = body.get('text', '')

    if not raw_text or len(raw_text.strip()) < 5:
        print(f"⚠️ [AI] Skipping {fid}: Text too short or empty.")
        return {"status": "skipped", "message": "Insufficient text"}

    print(f"🌟 [AI] Starting Mistral Analysis for: {fid}")
    
    api_key = os.environ.get('MISTRAL_API_KEY')
    url = "https://api.mistral.ai/v1/chat/completions"
    
    payload = {
        "model": "mistral-medium-latest",
        "messages": [{"role": "user", "content": f"Analyze this feedback: {raw_text}. Return JSON with 'summary' (1 sentence) and 'sentiment' (POSITIVE/NEGATIVE/NEUTRAL)."}],
        "response_format": {"type": "json_object"} 
    }

    try:
        # 1. Call AI
        response = requests.post(url, json=payload, 
                                 headers={"Authorization": f"Bearer {api_key}"}, 
                                 timeout=30)
        response.raise_for_status()
        
        # 2. Parse Cleanly
        res_json = response.json()
        raw_content = res_json['choices'][0]['message']['content'].strip()
        # Remove any markdown artifacts
        clean_content = raw_content.replace('```json', '').replace('```', '').strip()
        ai_data = json.loads(clean_content)
        
        # 3. 💾 UPDATE DB (Atomic Update)
        print(f"💾 [AI] Finalizing Record: {fid}")
        table.update_item(
            Key={'feedback_id': fid},
            UpdateExpression="SET summary = :s, sentiment = :sent, #st = :status",
            ExpressionAttributeValues={
                ':s': ai_data.get('summary', 'No summary.'),
                ':sent': ai_data.get('sentiment', 'NEUTRAL').upper(),
                ':status': 'COMPLETED'
            },
            ExpressionAttributeNames={'#st': 'status'}
        )
        
        print(f"✅ [AI] Successfully completed {fid}")
        # 🚀 NEW RELAY: Trigger Speech Generation
        print(f"🎙️ [AI] Relaying {fid} to Speech Worker...")
        try:
            requests.post(
                "http://localhost:5001/process-speech", 
                json={
                    "body": {
                        "feedback_id": fid,
                        "text": ai_data.get('summary', 'Analysis complete.'), # Speak the summary
                        "language": "en"
                    }
                },
                timeout=0.1 
            )
        except requests.exceptions.ReadTimeout:
            pass
        return {"status": "success", "feedback_id": fid}

    except Exception as e:
        print(f"🔥 [AI-ERROR] {fid}: {str(e)}")
        return {"status": "error", "message": str(e)}