import boto3
import json
import os
import datetime

translate = boto3.client('translate', region_name='us-east-1')
comprehend = boto3.client('comprehend', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
lambda_client = boto3.client('lambda', region_name='us-east-1')

def lambda_handler(event, context):
    fid = event.get('feedback_id')
    raw_text = event.get('text', '')

    try:
        # 1. Translate
        tr_res = translate.translate_text(Text=raw_text, SourceLanguageCode='auto', TargetLanguageCode='en')
        eng_text = tr_res['TranslatedText']
        src_lang = tr_res['SourceLanguageCode']

        # 2. Sentiment
        comp_lang = src_lang if src_lang in ['en', 'es', 'fr', 'de', 'it', 'pt'] else 'en'
        sent_res = comprehend.detect_sentiment(Text=raw_text, LanguageCode=comp_lang)

        # 3. Save Initial Analysis
        dynamodb.Table('Analysis_Summaries').put_item(Item={
            'feedback_id': fid,
            'sentiment': sent_res['Sentiment'],
            'language': src_lang,
            'original_text': raw_text,
            'translated_text': eng_text,
            'status': 'ANALYZED'
        })

        # 4. RELAY: Trigger Summarizer Worker
        lambda_client.invoke(
            FunctionName='summarizer_worker',
            InvocationType='Event',
            Payload=json.dumps({"feedback_id": fid, "text": eng_text}).encode('utf-8')
        )

        return {"status": "success"}
    except Exception as e:
        print(f"❌ Analysis Error: {e}")
        return {"status": "error"}