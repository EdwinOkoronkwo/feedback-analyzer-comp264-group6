import boto3
import json
import os
import time

translate = boto3.client('translate', region_name='us-east-1')
comprehend = boto3.client('comprehend', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
lambda_client = boto3.client('lambda', region_name='us-east-1')

def lambda_handler(event, context):
    fid = event.get('feedback_id')
    raw_text = event.get('text', '')

    if not raw_text:
        print(f"⚠️ No text found for {fid}")
        return {"status": "error", "message": "No text to analyze"}

    try:
        # 1. Translate to English (Centralizes logic for Mistral/LLM)
        tr_res = translate.translate_text(
            Text=raw_text, 
            SourceLanguageCode='auto', 
            TargetLanguageCode='en'
        )
        eng_text = tr_res['TranslatedText']
        src_lang = tr_res['SourceLanguageCode']

        # 2. Sentiment Analysis (Performed on English for highest accuracy)
        sent_res = comprehend.detect_sentiment(Text=eng_text, LanguageCode='en')
        sentiment = sent_res['Sentiment']

        # 3. UPDATE DynamoDB (Preserving metadata from previous workers)
        table = dynamodb.Table('Analysis_Summaries')
        table.update_item(
            Key={'feedback_id': fid},
            UpdateExpression="SET sentiment = :s, src_lang = :l, translated_text = :t, #st = :stat, master = :m",
            ExpressionAttributeNames={'#st': 'status'},
            ExpressionAttributeValues={
                ':s': sentiment,
                ':l': src_lang,
                ':t': eng_text,
                ':stat': 'ANALYZED',
                ':m': f"🧠 {src_lang.upper()} -> EN | Sentiment: {sentiment}"
            }
        )

        # 4. RELAY: Trigger Summarizer Worker
        print(f"📡 [ANALYSIS] Handing off {fid} to Summarizer...")
        lambda_client.invoke(
            FunctionName='summarizer_worker', # Ensure this matches your AWS console name
            InvocationType='Event',
            Payload=json.dumps({"feedback_id": fid, "text": eng_text}).encode('utf-8')
        )

        return {"status": "success", "feedback_id": fid}
        
    except Exception as e:
        print(f"❌ Analysis Error for {fid}: {str(e)}")
        # Update status to help UI debugging
        try:
            dynamodb.Table('Analysis_Summaries').update_item(
                Key={'feedback_id': fid},
                UpdateExpression="SET #st = :err",
                ExpressionAttributeNames={'#st': 'status'},
                ExpressionAttributeValues={':err': 'ANALYSIS_FAILED'}
            )
        except: pass
        return {"status": "error", "message": str(e)}