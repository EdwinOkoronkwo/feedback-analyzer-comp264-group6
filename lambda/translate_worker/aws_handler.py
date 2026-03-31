import boto3

translate = boto3.client('translate')

def lambda_handler(event, context):
    raw_text = event.get('raw_text', '')
    fid = event.get('feedback_id')

    if not raw_text:
        # If no text was found, pass an empty string instead of crashing
        return {**event, "text": "", "status": "NO_TEXT_TO_TRANSLATE"}

    try:
        # Translate to English (Auto-detects source language)
        response = translate.translate_text(
            Text=raw_text,
            SourceLanguageCode='auto',
            TargetLanguageCode='en'
        )

        # Merge the new 'text' into the existing event data
        return {
            **event,
            "text": response['TranslatedText'],
            "source_lang": response['SourceLanguageCode'],
            "status": "TRANSLATION_COMPLETED"
        }
    except Exception as e:
        print(f"❌ Translate Error: {str(e)}")
        raise e