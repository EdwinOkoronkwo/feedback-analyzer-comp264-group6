import boto3
import os
import time

polly = boto3.client('polly')
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    fid = event.get('feedback_id')
    summary = event.get('summary', 'No summary provided')
    bucket = os.environ.get('S3_BUCKET_NAME', 'comp264-edwin-1772030214')

    try:
        # 1. Synthesize Speech
        response = polly.synthesize_speech(
            Text=summary,
            OutputFormat='mp3',
            VoiceId='Joanna'
        )

        # 2. Save MP3 to S3
        audio_key = f"audio/{fid}.mp3"
        s3.put_object(
            Bucket=bucket,
            Key=audio_key,
            Body=response['AudioStream'].read(),
            ContentType='audio/mpeg'
        )

        audio_url = f"s3://{bucket}/{audio_key}"

        # 3. Final Database Update
        table = dynamodb.Table('Analysis_Summaries')
        table.update_item(
            Key={'feedback_id': fid},
            # 🎯 FIX: Match the 'audio_url' key and the 'COMPLETED' status
            UpdateExpression="SET audio_url = :url, #s = :stat",
            ExpressionAttributeNames={'#s': 'status'},
            ExpressionAttributeValues={
                ':url': audio_url,
                ':stat': 'COMPLETED'  # <--- THE MAGIC WORD
            }
        )

        return {
            **event,
            "audio_url": audio_url,
            "status": "COMPLETED" # Match here too for Step Function logs
        }

    except Exception as e:
        print(f"❌ Speech Error: {str(e)}")
        raise e