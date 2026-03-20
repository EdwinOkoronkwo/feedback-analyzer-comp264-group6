import boto3
import os
import json

# Initialize Clients
polly = boto3.client('polly', region_name='us-east-1')
s3 = boto3.client('s3', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

# Configuration
BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'comp264-edwin-1772030214')
SUMMARIES_TABLE = os.environ.get('SUMMARIES_TABLE', 'Analysis_Summaries')
table = dynamodb.Table(SUMMARIES_TABLE)

def lambda_handler(event, context):
    # 1. Handle Input (Triggered by summarizer_worker)
    # 🎯 NOTE: Ensure the keys match what your summarizer sends
    fid = event.get('feedback_id', 'unknown')
    raw_text = event.get('text_to_speak') or event.get('text', '')
    lang_code = event.get('language', 'en') 

    if not raw_text or raw_text in ["", "No readable text found.", "N/A"]:
        print(f"⚠️ Skipping speech for {fid}: No valid text.")
        return {"status": "skipped", "message": "No text to speak"}

    print(f"🎙️ Speech Worker: Generating Polly audio for {fid} ({lang_code})")

    voice_map = {
        'fr': 'Celine', 
        'es': 'Conchita', 
        'de': 'Vicki', 
        'it': 'Carla', 
        'en': 'Joanna' 
    }
    voice_id = voice_map.get(lang_code[:2], 'Joanna') 

    try:
        # 2. Request Speech Generation
        polly_response = polly.synthesize_speech(
            Text=raw_text,
            OutputFormat='mp3',
            VoiceId=voice_id,
            Engine='neural' if voice_id in ['Joanna', 'Vicki'] else 'standard' # Neural sounds better!
        )

        # 3. Stream Audio to S3
        audio_key = f"audio/{fid}.mp3"
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=audio_key,
            Body=polly_response['AudioStream'].read(),
            ContentType='audio/mpeg'
        )

        # 4. 🎯 THE FIX: Generate a Presigned URL
        # This creates a temporary 1-hour link that Streamlit can play
        presigned_url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': BUCKET_NAME, 'Key': audio_key},
            ExpiresIn=3600 # 1 Hour
        )

        # 5. Update Analysis_Summaries with the ACCESS KEY
        table.update_item(
            Key={'feedback_id': fid},
            UpdateExpression="SET audio_path = :val, polly_voice = :voice, speech_status = :status",
            ExpressionAttributeValues={
                ':val': presigned_url,
                ':voice': voice_id,
                ':status': 'COMPLETED'
            }
        )

        print(f"✅ Speech Success for {fid}: Presigned URL saved to DB.")
        return {"status": "success", "audio_url": presigned_url}

    except Exception as e:
        print(f"❌ Speech Error for {fid}: {str(e)}")
        table.update_item(
            Key={'feedback_id': fid},
            UpdateExpression="SET speech_status = :status",
            ExpressionAttributeValues={':status': f"ERROR: {str(e)[:50]}"}
        )
        return {"status": "error", "message": str(e)}