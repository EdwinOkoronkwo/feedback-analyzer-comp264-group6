import boto3
import time
from botocore.exceptions import ClientError

# --- CONFIGURATION (Must match your deploy script) ---
REGION = "us-east-1"
ROLE_NAME = "FeedbackAnalyzerRole"
BUCKET_NAME = "comp264-edwin-1772030214"
STATE_MACHINE_NAME = "Kaggle_Tobacco_Pipeline" # Update this to your SFN name

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

# Initialize Clients
lambda_client = boto3.client('lambda', region_name=REGION)
dynamodb = boto3.client('dynamodb', region_name=REGION)
iam = boto3.client('iam')
s3 = boto3.resource('s3', region_name=REGION)
sfn = boto3.client('stepfunctions', region_name=REGION)

def destroy_system():
    print("\n🧨 INITIALIZING FULL SYSTEM TEARDOWN...")
    print("------------------------------------------")

    # 1. Delete Step Functions (The Orchestrator)
    try:
        print(f"🗑️  Looking for Step Function: {STATE_MACHINE_NAME}...")
        response = sfn.list_state_machines()
        for sm in response['stateMachines']:
            if sm['name'] == STATE_MACHINE_NAME:
                sfn.delete_state_machine(stateMachineArn=sm['stateMachineArn'])
                print(f"✅ State Machine {STATE_MACHINE_NAME} removal initiated.")
    except Exception as e:
        print(f"ℹ️  Step Function skip: {str(e)}")

    # 2. Delete Lambda Functions
    for name in WORKERS:
        try:
            print(f"🗑️  Deleting Lambda: {name}...")
            lambda_client.delete_function(FunctionName=name)
            print(f"✅ {name} removed.")
        except ClientError as e:
            print(f"ℹ️  {name} skip: {e.response['Error']['Message']}")

    # 3. Delete DynamoDB Tables
    for table in TABLES:
        try:
            print(f"🗑️  Deleting Table: {table}...")
            dynamodb.delete_table(TableName=table)
            print(f"✅ {table} removal initiated.")
        except ClientError as e:
            print(f"ℹ️  {table} skip: {e.response['Error']['Message']}")

    # 4. Empty and Delete S3 Bucket (Optional - Use with caution)
    try:
        print(f"🗑️  Emptying Bucket: {BUCKET_NAME}...")
        bucket = s3.Bucket(BUCKET_NAME)
        bucket.objects.all().delete()
        # Uncomment below if you want to delete the bucket itself:
        # bucket.delete() 
        print(f"✅ {BUCKET_NAME} content purged.")
    except Exception as e:
        print(f"ℹ️  S3 skip: {str(e)}")

    # 5. Robust IAM Role Cleanup
    try:
        print(f"🗑️  Cleaning up IAM Role: {ROLE_NAME}...")
        # We must detach ALL policies before deleting the role
        attached_policies = iam.list_attached_role_policies(RoleName=ROLE_NAME)
        for policy in attached_policies['AttachedPolicies']:
            print(f"   - Detaching {policy['PolicyName']}...")
            iam.detach_role_policy(RoleName=ROLE_NAME, PolicyArn=policy['PolicyArn'])
        
        iam.delete_role(RoleName=ROLE_NAME)
        print(f"✅ IAM Role {ROLE_NAME} fully removed.")
    except ClientError as e:
        print(f"ℹ️  Role skip: {e.response['Error']['Message']}")

    print("\n💥 TEARDOWN COMPLETE. AWS Environment is now empty.")

if __name__ == "__main__":
    print("⚠️  WARNING: This will permanently delete ALL data, workers, and infrastructure.")
    confirm = input("Are you sure? Type 'DESTROY' to proceed: ")
    if confirm == 'DESTROY':
        destroy_system()
    else:
        print("Teardown aborted. No resources were harmed.")