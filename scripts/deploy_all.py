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

# 🎯 UPDATED: Added kag_worker and mnist_ingestor_worker
WORKERS = [
    ("master_worker", "lambda/master_worker/aws_handler.py", "aws_handler.lambda_handler"),
    ("ocr_worker", "lambda/ocr_worker/aws_handler.py", "aws_handler.lambda_handler"),
    ("analysis_worker", "lambda/analysis_worker/aws_handler.py", "aws_handler.lambda_handler"),
    ("summarizer_worker", "lambda/summary_worker/aws_handler.py", "aws_handler.lambda_handler"),
    ("speech_worker", "lambda/speech_worker/aws_handler.py", "aws_handler.lambda_handler"),
    ("kag_worker", "lambda/kag_worker/aws_handler.py", "aws_handler.lambda_handler"), # 📄 New Kaggle Worker
    ("mnist_ingestor_worker", "lambda/mnist_worker/aws_handler.py", "aws_handler.lambda_handler")
]

lambda_client = boto3.client('lambda', region_name=REGION)
s3 = boto3.client('s3', region_name=REGION)
dynamodb = boto3.client('dynamodb', region_name=REGION)
iam = boto3.client('iam')

def create_zip(src, output_name):
    if not os.path.exists(src):
        print(f"⚠️  SKIPPING: Source file not found: {src}")
        return None
    with zipfile.ZipFile(output_name, 'w') as z:
        z.write(src, 'aws_handler.py')
    with open(output_name, 'rb') as f:
        return f.read()

def wait_for_lambda(name):
    print(f"⏳ Waiting for {name} to stabilize...")
    waiter = lambda_client.get_waiter('function_updated_v2')
    waiter.wait(FunctionName=name)

def deploy():
    print("🏗️  Building Full Production Environment...")

    # 1. IAM Role Setup
    try:
        policy = {"Version": "2012-10-17", "Statement": [{"Action": "sts:AssumeRole", "Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}}]}
        iam.create_role(RoleName=ROLE_NAME, AssumeRolePolicyDocument=json.dumps(policy))
        iam.attach_role_policy(RoleName=ROLE_NAME, PolicyArn='arn:aws:iam::aws:policy/AdministratorAccess')
        print("✅ IAM Role Ready.")
        time.sleep(5) 
    except ClientError:
        print("ℹ️  Role exists.")

    # 2. Infrastructure (S3 & Dynamo)
    try:
        s3.create_bucket(Bucket=BUCKET_NAME)
        print(f"✅ S3 Bucket {BUCKET_NAME} Ready.")
    except ClientError: pass

    for table in [TABLE_NAME, USER_TABLE]:
        try:
            key = 'feedback_id' if table == TABLE_NAME else 'username'
            dynamodb.create_table(
                TableName=table,
                KeySchema=[{'AttributeName': key, 'KeyType': 'HASH'}],
                AttributeDefinitions=[{'AttributeName': key, 'AttributeType': 'S'}],
                BillingMode='PAY_PER_REQUEST'
            )
            print(f"✅ Table {table} Created.")
        except ClientError: pass

    # 3. Worker Deployment Loop
    role_arn = iam.get_role(RoleName=ROLE_NAME)['Role']['Arn']
    for name, src, handler in WORKERS:
        zip_bytes = create_zip(src, f"{name}.zip")
        if zip_bytes is None: continue # Skip missing local files
        
        layers = [REQUESTS_LAYER] if "summarizer" in name else []
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
                Timeout=60, 
                MemorySize=256,
                Environment=env_vars,
                Layers=layers
            )
            print(f"✅ {name} created.")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceConflictException':
                print(f"🔄 Updating {name}...")
                wait_for_lambda(name)
                lambda_client.update_function_configuration(
                    FunctionName=name, Environment=env_vars, Layers=layers
                )
                wait_for_lambda(name)
                lambda_client.update_function_code(FunctionName=name, ZipFile=zip_bytes)
                print(f"✅ {name} updated.")

    print("\n✨ SYSTEM ONLINE. All workers (including Kaggle) are deployed.")

if __name__ == "__main__":
    deploy()