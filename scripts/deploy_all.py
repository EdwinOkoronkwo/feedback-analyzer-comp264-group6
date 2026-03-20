import boto3
import zipfile
import os
import json
import time
from dotenv import load_dotenv
from botocore.exceptions import ClientError

load_dotenv()

# --- CONFIGURATION ---
REGION = "us-east-1"
ROLE_NAME = "FeedbackAnalyzerRole"
BUCKET_NAME = "comp264-edwin-1772030214"
TABLE_NAME = "Analysis_Summaries"
USER_TABLE = "Feedback_Users" 
MISTRAL_KEY = os.getenv("MISTRAL_API_KEY")
REQUESTS_LAYER = 'arn:aws:lambda:us-east-1:770693421928:layer:Klayers-p39-requests:19'

LAMBDA_TIMEOUT = 60
LAMBDA_MEMORY = 256

WORKERS = [
    ("master_worker", "lambda/master_worker/aws_handler.py", "aws_handler.lambda_handler"),
    ("ocr_worker", "lambda/ocr_worker/aws_handler.py", "aws_handler.lambda_handler"),
    ("analysis_worker", "lambda/analysis_worker/aws_handler.py", "aws_handler.lambda_handler"),
    ("summarizer_worker", "lambda/summary_worker/aws_handler.py", "aws_handler.lambda_handler"),
    ("speech_worker", "lambda/speech_worker/aws_handler.py", "aws_handler.lambda_handler")
]

lambda_client = boto3.client('lambda', region_name=REGION)
s3 = boto3.client('s3', region_name=REGION)
dynamodb = boto3.client('dynamodb', region_name=REGION)
iam = boto3.client('iam')

def create_zip(src, output_name):
    with zipfile.ZipFile(output_name, 'w') as z:
        z.write(src, 'aws_handler.py')
    with open(output_name, 'rb') as f:
        return f.read()

def wait_for_lambda(name):
    print(f"⏳ Waiting for {name} to stabilize...")
    waiter = lambda_client.get_waiter('function_updated_v2')
    waiter.wait(FunctionName=name)

def add_s3_trigger(lambda_name, bucket_name):
    print(f"🔗 Linking S3 Bucket to {lambda_name}...")
    try:
        lambda_client.add_permission(
            FunctionName=lambda_name,
            StatementId='s3-trigger-permission',
            Action='lambda:InvokeFunction',
            Principal='s3.amazonaws.com',
            SourceArn=f'arn:aws:s3:::{bucket_name}'
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceConflictException':
            print("ℹ️ S3 Permission already exists.")

    s3_resource = boto3.resource('s3')
    bucket_notification = s3_resource.BucketNotification(bucket_name)
    try:
        bucket_notification.put(
            NotificationConfiguration={
                'LambdaFunctionConfigurations': [
                    {
                        'LambdaFunctionArn': lambda_client.get_function(FunctionName=lambda_name)['Configuration']['FunctionArn'],
                        'Events': ['s3:ObjectCreated:*'],
                        'Filter': {'Key': {'FilterRules': [{'Name': 'prefix', 'Value': 'uploads/'}]}}
                    }
                ]
            }
        )
        print(f"✅ S3 Trigger Active: {bucket_name} -> {lambda_name}")
    except Exception as e:
        print(f"❌ Failed to set S3 Trigger: {e}")

def deploy():
    print("🏗️  Building Production Environment...")

    # 1. IAM Role
    try:
        policy = {"Version": "2012-10-17", "Statement": [{"Action": "sts:AssumeRole", "Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}}]}
        iam.create_role(RoleName=ROLE_NAME, AssumeRolePolicyDocument=json.dumps(policy))
        iam.attach_role_policy(RoleName=ROLE_NAME, PolicyArn='arn:aws:iam::aws:policy/AdministratorAccess')
        print("✅ IAM Role Ready.")
        time.sleep(5) 
    except ClientError:
        print("ℹ️ Role exists.")

    # 2. S3 Bucket
    try:
        print(f"📡 Ensuring S3 Bucket exists: {BUCKET_NAME}...")
        s3.create_bucket(Bucket=BUCKET_NAME)
        waiter = s3.get_waiter('bucket_exists')
        waiter.wait(Bucket=BUCKET_NAME)
        print("✅ S3 Bucket is ACTIVE.")
    except ClientError as e:
        print(f"ℹ️ S3 Bucket info: {e}")

    # 3. DynamoDB Tables
    for table in [TABLE_NAME, USER_TABLE]:
        try:
            key = 'feedback_id' if table == TABLE_NAME else 'username'
            print(f"📡 Creating {table}...")
            dynamodb.create_table(
                TableName=table,
                KeySchema=[{'AttributeName': key, 'KeyType': 'HASH'}],
                AttributeDefinitions=[{'AttributeName': key, 'AttributeType': 'S'}],
                BillingMode='PAY_PER_REQUEST'
            )
            waiter = dynamodb.get_waiter('table_exists')
            waiter.wait(TableName=table)
            print(f"✅ Table {table} is ACTIVE.")
        except ClientError:
            print(f"ℹ️ Table {table} exists.")

    # 4. Seed Admin User
    print("👤 Seeding Admin User...")
    try:
        dynamodb.put_item(
            TableName=USER_TABLE,
            Item={'username': {'S': 'admin'}, 'role': {'S': 'admin'}, 'password_hash': {'S': 'SECRET_HASH'}}
        )
        print("✅ Admin seeded.")
    except Exception as e:
        print(f"⚠️ Seed error: {e}")

    # 5. Deploy Workers
    role_arn = iam.get_role(RoleName=ROLE_NAME)['Role']['Arn']
    for name, src, handler in WORKERS:
        zip_bytes = create_zip(src, f"{name}.zip")
        
        # Determine layers - only the summarizer needs requests
        layers = [REQUESTS_LAYER] if "summarizer" in name else []
        
        # Define shared environment variables
        env_vars = {
            'Variables': {
                'MISTRAL_API_KEY': MISTRAL_KEY or "",
                'SUMMARIES_TABLE': TABLE_NAME,
                'S3_BUCKET_NAME': BUCKET_NAME
            }
        }

        try:
            print(f"📦 Deploying {name}...")
            lambda_client.create_function(
                FunctionName=name, 
                Runtime='python3.9', 
                Role=role_arn,
                Handler=handler, 
                Code={'ZipFile': zip_bytes},
                Timeout=LAMBDA_TIMEOUT, 
                MemorySize=LAMBDA_MEMORY,
                Environment=env_vars,
                Layers=layers  # Fixed placement
            )
            print(f"✅ {name} created.")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceConflictException':
                print(f"🔄 Updating {name}...")
                wait_for_lambda(name)
                # Update Config (Timeout, Memory, Env, Layers)
                lambda_client.update_function_configuration(
                    FunctionName=name, 
                    Timeout=LAMBDA_TIMEOUT, 
                    MemorySize=LAMBDA_MEMORY,
                    Environment=env_vars,
                    Layers=layers
                )
                wait_for_lambda(name)
                # Update Code
                lambda_client.update_function_code(FunctionName=name, ZipFile=zip_bytes)
                print(f"✅ {name} updated.")

    # 6. Setup S3 Trigger for ocr_worker
    add_s3_trigger("master_worker", BUCKET_NAME)

    print("\n✨ SYSTEM ONLINE.")

if __name__ == "__main__":
    deploy()