import boto3
import time
from botocore.exceptions import ClientError

# --- CONFIGURATION (Must match your deploy script) ---
REGION = "us-east-1"
ROLE_NAME = "FeedbackAnalyzerRole"
TABLES = ["Analysis_Summaries", "Feedback_Users"]
WORKERS = [
    "master_worker", 
    "ocr_worker", 
    "analysis_worker", 
    "summarizer_worker", 
    "speech_worker", 
    "kag_worker", 
    "mnist_ingestor_worker"
]

lambda_client = boto3.client('lambda', region_name=REGION)
dynamodb = boto3.client('dynamodb', region_name=REGION)
iam = boto3.client('iam')

def destroy_system():
    print("🧨 Initializing Full System Teardown...")

    # 1. Delete Lambda Functions
    for name in WORKERS:
        try:
            print(f"🗑️  Deleting Lambda: {name}...")
            lambda_client.delete_function(FunctionName=name)
            print(f"✅ {name} removed.")
        except ClientError as e:
            print(f"ℹ️  {name} skip: {e.response['Error']['Message']}")

    # 2. Delete DynamoDB Tables
    for table in TABLES:
        try:
            print(f"🗑️  Deleting Table: {table}...")
            dynamodb.delete_table(TableName=table)
            print(f"✅ {table} removal initiated.")
        except ClientError as e:
            print(f"ℹ️  {table} skip: {e.response['Error']['Message']}")

    # 3. Cleanup IAM Role
    try:
        print(f"🗑️  Detaching policies and deleting Role: {ROLE_NAME}...")
        # Detach the Admin policy first
        iam.detach_role_policy(
            RoleName=ROLE_NAME, 
            PolicyArn='arn:aws:iam::aws:policy/AdministratorAccess'
        )
        # Delete the role
        iam.delete_role(RoleName=ROLE_NAME)
        print(f"✅ IAM Role {ROLE_NAME} fully removed.")
    except ClientError as e:
        print(f"ℹ️  Role skip: {e.response['Error']['Message']}")

    print("\n💥 TEARDOWN COMPLETE. AWS Environment is now empty.")

if __name__ == "__main__":
    print("⚠️  WARNING: This will permanently delete ALL data and workers.")
    confirm = input("Are you sure? Type 'DESTROY' to proceed: ")
    if confirm == 'DESTROY':
        destroy_system()
    else:
        print("Teardown aborted. No resources were harmed.")