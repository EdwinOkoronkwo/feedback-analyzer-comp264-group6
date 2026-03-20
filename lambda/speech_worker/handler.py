import os
import time
from gtts import gTTS
from scripts.db_config import get_dynamodb_resource

# Initialize Local DynamoDB
dynamodb = get_dynamodb_resource()
# 🎯 FIX 1: Align with your actual local table name
table = dynamodb.Table('Metadata')

def lambda_handler(event, context):
    """
    Local Speech Worker: Replaces Polly with gTTS.
    Saves audio to a local 'static/audio/' folder.
    """
    # 1. Setup Local Storage
    audio_output_dir = "static/audio" 
    if not os.path.exists(audio_output_dir):
        os.makedirs(audio_output_dir)

    records_to_process = []
    
    # 2. Handle Input
    if 'Records' in event:
        for record in event['Records']:
            if record['eventName'] in ['INSERT', 'MODIFY']:
                new_image = record['dynamodb'].get('NewImage', {})
                records_to_process.append({
                    'fid': new_image.get('feedback_id', {}).get('S'),
                    'lang': new_image.get('language', {}).get('S', 'en'),
                    'text': new_image.get('translated_text', {}).get('S')
                })
    else:
        # Direct call from Flask bridge
        body = event.get('body', {})
        fid = body.get('feedback_id', 'unknown')
        text = body.get('text')
        lang = body.get('language', 'en')
        
        if text:
            records_to_process.append({
                'fid': fid,
                'lang': lang,
                'text': text
            })

    last_audio_path = ""
    last_fid = "unknown"

    # 3. Generate Speech
    for item in records_to_process:
        fid = item['fid']
        lang = item['lang']
        text = item['text']
        last_fid = fid

        if not text:
            continue

        try:
            print(f"🎙️ Generating {lang} speech for {fid} locally...")
            
            tts = gTTS(text=text, lang=lang)
            
            # 🎯 FIX 2: Use the ID directly (cleaner than splitting)
            filename = f"{fid}_{lang}.mp3"
            file_path = os.path.join(audio_output_dir, filename)
            
            tts.save(file_path)
            last_audio_path = file_path

            # 4. Update Local DynamoDB (Metadata Table)
            # 🎯 FIX 3: Use feedback_id as primary key to match your schema
            table.put_item(Item={
                'feedback_id': fid,
                'type': f'audio_{lang}',
                'audio_path': file_path,
                'processed_at': str(time.time()),
                'engine': 'gtts_local'
            })
            
            print(f"✅ Audio saved locally: {file_path}")

        except Exception as e:
            print(f"❌ Speech Generation Error for {fid}: {str(e)}")

    # 🎯 RETURN DICT: Pass the audio path back to the Flask bridge
    return {
        "status": "success", 
        "feedback_id": last_fid, 
        "audio_path": last_audio_path
    }