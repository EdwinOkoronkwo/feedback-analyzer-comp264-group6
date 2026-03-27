import boto3
import uuid

def force_realtime_s3_check():
    s3 = boto3.client('s3', region_name='us-east-1')
    bucket = "comp264-edwin-1772030214"
    unique_id = f"verification_{uuid.uuid4().hex[:6]}"
    
    print(f"📡 Sending unique file: {unique_id}.json")
    
    try:
        s3.put_object(
            Bucket=bucket,
            Key=f"live-data/{unique_id}.json",
            Body='{"status": "manual_verify", "timezone": "MST"}'
        )
        
        # Now list and check the very latest file
        objs = s3.list_objects_v2(Bucket=bucket, Prefix='live-data/')
        latest = sorted(objs['Contents'], key=lambda x: x['LastModified'], reverse=True)[0]
        
        print(f"\n✅ SUCCESS!")
        print(f"📄 Newest File in Bucket: {latest['Key']}")
        print(f"🕒 Timestamp (UTC): {latest['LastModified']}")
        print(f"💡 That equals: {latest['LastModified'] - datetime.timedelta(hours=7)} (MST/Edmonton)")
        
    except Exception as e:
        print(f"❌ S3 Write Failed: {e}")

if __name__ == "__main__":
    import datetime
    force_realtime_s3_check()