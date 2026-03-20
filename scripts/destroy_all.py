import boto3
import zipfile
import os
import json
import time
from dotenv import load_dotenv
from botocore.exceptions import ClientError

# Load Mistral Key from .env
load_dotenv()

# --- CONFIGURATION ---
REGION = "us-east-1"
ROLE_NAME = "FeedbackAnalyzerRole"
BUCKET_NAME = "comp264-edwin-1772030214"
TABLE_NAME = "Analysis_Summaries"
USER_TABLE = "Feedback_Users" 
MISTRAL_KEY = os.getenv("MISTRAL_API_KEY")
REQUESTS_LAYER = 'arn:aws:lambda:us-east-1:770693421928:layer:Klayers-p39-requests:19'

# Power Settings
LAMBDA_TIMEOUT = 60  
LAMBDA_MEMORY = 256  

WORKERS = [
    ("ocr_worker", "lambda/ocr_worker/aws_handler.py", "aws_handler.lambda_handler"),
    ("analysis_worker", "lambda/analysis_worker/aws_handler.py", "aws_handler.lambda_handler"),
    ("summarizer_worker", "lambda/summary_worker/aws_handler.py", "aws_handler.lambda_handler"),
    ("speech_worker", "lambda/speech_worker/aws_handler.py", "aws_handler.lambda_handler")
]

# Initialize Clients
lambda_client = boto3.client('lambda', region_name=REGION)
s3 = boto3.client('s3', region_name=REGION)
dynamodb = boto3.client('dynamodb', region_name=REGION)
iam = boto3.client('iam')

def create_zip(src, output_name):
    """Zips the handler file for Lambda deployment."""
    with zipfile.ZipFile(output_name, 'w') as z:
        z.write(src, 'aws_handler.py')
    with open(output_name, 'rb') as f:
        return f.read()

def wait_for_lambda(name):
    """Pauses execution until the Lambda function is in an 'Active' state."""
    print(f"⏳ Waiting for {name} to stabilize...")
    try:
        waiter = lambda_client.get_waiter('function_updated_v2')
        waiter.wait(FunctionName=name, WaiterConfig={'Delay': 2, 'MaxAttempts': 20})
    except Exception as e:
        print(f"ℹ️ Stabilization wait finished: {e}")

def deploy():
    print("🏗️  Building Production Environment...")

    # 1. IAM Role Setup
    try:
        policy = {
            "Version": "2012-10-17", 
            "Statement": [{
                "Action": "sts:AssumeRole", 
                "Effect": "Allow", 
                "Principal": {"Service": "lambda.amazonaws.com"}
            }]
        }
        iam.create_role(RoleName=ROLE_NAME, AssumeRolePolicyDocument=json.dumps(policy))
        iam.attach_role_policy(RoleName=ROLE_NAME, PolicyArn='arn:aws:iam::aws:policy/AdministratorAccess')
        print("✅ IAM Role Ready. Waiting for propagation...")
        time.sleep(10) 
    except ClientError: 
        print("ℹ️ Role already exists.")

    # 2. S3 Bucket Creation with Waiter
    try:
        print(f"📡 Ensuring S3 Bucket exists: {BUCKET_NAME}")
        s3.create_bucket(Bucket=BUCKET_NAME)
        s3_waiter = s3.get_waiter('bucket_exists')
        s3_waiter.wait(Bucket=BUCKET_NAME)
        print(f"✅ S3 Bucket {BUCKET_NAME} is ACTIVE.")
    except ClientError as e:
        if e.response['Error']['Code'] in ['BucketAlreadyOwnedByYou', 'BucketAlreadyExists']:
            print(f"ℹ️ S3 Bucket {BUCKET_NAME} already exists.")
        else:
            print(f"❌ S3 Error: {e}")

    # 3. DynamoDB Tables with Waiters
    for table in [TABLE_NAME, USER_TABLE]:
        try:
            key = 'feedback_id' if table == TABLE_NAME else 'username'
            dynamodb.create_table(
                TableName=table,
                KeySchema=[{'AttributeName': key, 'KeyType': 'HASH'}],
                AttributeDefinitions=[{'AttributeName': key, 'AttributeType': 'S'}],
                BillingMode='PAY_PER_REQUEST'
            )
            print(f"📡 Creating table {table}...")
            db_waiter = dynamodb.get_waiter('table_exists')
            db_waiter.wait(TableName=table)
            print(f"✅ Table {table} is ACTIVE.")
        except ClientError: 
            print(f"ℹ️ Table {table} already exists.")

    # 4. Seed Admin User
    print("👤 Seeding Admin User...")
    try:
        dynamodb.put_item(
            TableName=USER_TABLE,
            Item={
                'username': {'S': 'admin'},
                'role': {'S': 'admin'},
                'password_hash': {'S': 'SECRET_HASH'} 
            }
        )
        print("✅ Admin user seeded in DynamoDB.")
    except Exception as e: 
        print(f"⚠️ Seed error: {e}")

    # 5. Deploy/Update Workers
    role_arn = iam.get_role(RoleName=ROLE_NAME)['Role']['Arn']
    for name, src, handler in WORKERS:
        zip_bytes = create_zip(src, f"{name}.zip")
        
        try:
            print(f"📦 Creating {name}...")
            lambda_client.create_function(
                FunctionName=name,
                Runtime='python3.9',
                Role=role_arn,
                Handler=handler,
                Code={'ZipFile': zip_bytes},
                Timeout=LAMBDA_TIMEOUT,
                MemorySize=LAMBDA_MEMORY,
                Environment={'Variables': {'MISTRAL_API_KEY': MISTRAL_KEY or ""}},
                Layers=[REQUESTS_LAYER] if "summarizer" in name else []
            )
            print(f"🚀 {name} deployed successfully.")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceConflictException':
                print(f"🔄 Updating existing {name} configuration...")
                wait_for_lambda(name)
                
                # Update Config
                lambda_client.update_function_configuration(
                    FunctionName=name,
                    Timeout=LAMBDA_TIMEOUT,
                    MemorySize=LAMBDA_MEMORY,
                    Environment={'Variables': {'MISTRAL_API_KEY': MISTRAL_KEY or ""}},
                    Layers=[REQUESTS_LAYER] if "summarizer" in name else []
                )
                
                # Wait for config to settle before code update
                wait_for_lambda(name)
                
                print(f"📤 Uploading new code to {name}...")
                lambda_client.update_function_code(FunctionName=name, ZipFile=zip_bytes)
                print(f"✅ {name} updated and ready.")
            else:
                print(f"❌ Error with {name}: {e}")

    print("\n✨ SYSTEM ONLINE. You can now launch Streamlit.")

if __name__ == "__main__":
    deploy()