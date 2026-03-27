import boto3

ID = "admin_1466833f"
BUCKET = "comp264-edwin-1772030214"

s3 = boto3.client('s3')
db = boto3.resource('dynamodb')

print(f"--- Checking AWS for {ID} ---")

# 1. Check S3
try:
    objs = s3.list_objects_v2(Bucket=BUCKET, Prefix=f"uploads/{ID}")
    if 'Contents' in objs:
        print(f"✅ S3: File found in uploads/ folder.")
    else:
        print(f"❌ S3: File NOT found. Pipeline might be uploading to the wrong path.")
except Exception as e:
    print(f"❌ S3 Error: {e}")

# 2. Check DynamoDB
try:
    table = db.Table('Analysis_Summaries')
    res = table.get_item(Key={'feedback_id': ID})
    if 'Item' in res:
        print(f"✅ DynamoDB: Record found! Status: {res['Item'].get('status')}")
    else:
        print(f"❌ DynamoDB: No record found for this ID. The Lambda didn't write to the table.")
except Exception as e:
    print(f"❌ DynamoDB Error: {e}")