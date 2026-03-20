import json
import time
import os
import requests
from scripts.db_config import get_dynamodb_resource

# Initialize the Local DynamoDB
dynamodb = get_dynamodb_resource()

# 🎯 FIX: Align with your actual local table name 'Metadata'
table = dynamodb.Table('Metadata')

def lambda_handler(event, context):
    api_key = os.environ.get('MISTRAL_API_KEY')
    target_langs = ['en'] 
    records_to_process = []
    
    # 1. Handle Input (Unify both Stream and Direct Call formats)
    if 'Records' in event:
        for record in event['Records']:
            if record['eventName'] in ['INSERT', 'MODIFY']:
                new_image = record['dynamodb'].get('NewImage', {})
                fid = new_image.get('feedback_id', {}).get('S')
                # Try to get text from different possible fields
                full_text = new_image.get('text', {}).get('S') or new_image.get('content', {}).get('S')
                if fid and full_text:
                    records_to_process.append({'fid': fid, 'text': full_text})
    else:
        # Direct call from Flask bridge
        body = event.get('body', {})
        if body.get('text'):
            records_to_process.append({
                'fid': body.get('feedback_id', 'unknown'),
                'text': body.get('text')
            })

    # 2. Process the records collected
    final_translated_text = ""
    last_fid = "unknown"

    for item in records_to_process:
        fid = item['fid']
        text = item['text']
        last_fid = fid
        
        for lang in target_langs:
            try:
                print(f"🌍 Translating {fid} to {lang} via Mistral...")
                
                prompt = f"Translate the following text to {lang}. Return ONLY the translated text: '{text}'"
                url = "https://api.mistral.ai/v1/chat/completions"
                headers = {"Authorization": f"Bearer {api_key}"}
                payload = {
                    "model": "mistral-medium-latest",
                    "messages": [{"role": "user", "content": prompt}]
                }
                
                response = requests.post(url, json=payload, headers=headers, timeout=15)
                response.raise_for_status()
                res_body = response.json()
                translated_text = res_body['choices'][0]['message']['content'].strip()
                
                if lang == 'en':
                    final_translated_text = translated_text

                # 3. Save to Local DynamoDB (Metadata Table)
                table.put_item(Item={
                    'feedback_id': fid,
                    'type': f'translation_{lang}',
                    'translated_text': translated_text,
                    'processed_at': str(time.time()),
                    'engine': 'mistral-medium-api'
                })
                print(f"✅ Saved {lang} translation for {fid} to Metadata")

            except Exception as e:
                print(f"❌ Translation Error ({lang}) for {fid}: {str(e)}")
                # If translation fails, pass the original text through so the chain doesn't break
                final_translated_text = text 

    # 🎯 RETURN DICT: Ensures Flask Bridge receives a dictionary with data
    return {
        "status": "success", 
        "feedback_id": last_fid, 
        "translated_text": final_translated_text or "Translation failed"
    }



# import boto3
# import time

# translate = boto3.client('translate')
# db = boto3.resource('dynamodb')

# def lambda_handler(event, context):
#     target_languages = ["es", "fr", "de", "it", "en"] 
    
#     for record in event['Records']:
#         if record['eventName'] in ['INSERT', 'MODIFY']:
#             new_image = record['dynamodb']['NewImage']
#             feedback_id = new_image['feedback_id']['S']
#             text_to_translate = " ".join([item['S'] for item in new_image['text_content']['L']])

#             for lang in target_languages:
#                 print(f"🌍 Translating [{feedback_id}] to {lang}...")
                
#                 result = translate.translate_text(
#                     Text=text_to_translate,
#                     SourceLanguageCode="auto",
#                     TargetLanguageCode=lang
#                 )

#                 # Each language gets its own row thanks to the Sort Key!
#                 db.Table("Analysis_Translations").put_item(Item={
#                     'feedback_id': feedback_id,
#                     'language': lang,
#                     'translated_text': result['TranslatedText'],
#                     'processed_at': str(time.time())
#                 })

#     return {"status": "success"}