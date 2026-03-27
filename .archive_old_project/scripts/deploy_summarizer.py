import boto3
import zipfile
import os
import time
from dotenv import load_dotenv  # 🎯 New import

# Load environment variables from .env file
load_dotenv()

lambda_client = boto3.client('lambda', region_name='us-east-1')
iam = boto3.client('iam')

# --- CONFIGURATION ---
FUNCTION_NAME = 'summarizer_worker'
SRC_FILE = 'lambda/summary_worker/aws_handler.py'
ROLE_NAME = 'FeedbackAnalyzerRole'

# 🎯 Pulling from environment instead of hardcoding
MISTRAL_KEY = os.getenv("MISTRAL_API_KEY") 

REQUESTS_LAYER = 'arn:aws:lambda:us-east-1:770693421928:layer:Klayers-p39-requests:19'
# ---------------------

def deploy():
    if not MISTRAL_KEY:
        print("❌ Error: MISTRAL_API_KEY not found in .env file.")
        return

    if not os.path.exists(SRC_FILE):
        print(f"❌ Error: {SRC_FILE} not found.")
        return

    # 1. Create Zip
    zip_path = 'summarizer.zip'
    with zipfile.ZipFile(zip_path, 'w') as z:
        z.write(SRC_FILE, 'aws_handler.py')

    with open(zip_path, 'rb') as f:
        zip_content = f.read()

    role_arn = iam.get_role(RoleName=ROLE_NAME)['Role']['Arn']

    try:
        # Update Code
        print(f"Uploading code to {FUNCTION_NAME}...")
        lambda_client.update_function_code(FunctionName=FUNCTION_NAME, ZipFile=zip_content)
        
        # Wait for update to stabilize
        print("⏳ Waiting for update to complete...")
        waiter = lambda_client.get_waiter('function_updated_v2')
        waiter.wait(FunctionName=FUNCTION_NAME)

        # Update Configuration (Pushing the Key to Lambda Environment)
        lambda_client.update_function_configuration(
            FunctionName=FUNCTION_NAME,
            Runtime='python3.9',
            Environment={'Variables': {'MISTRAL_API_KEY': MISTRAL_KEY}},
            Layers=[REQUESTS_LAYER]
        )
        print(f"✅ {FUNCTION_NAME} updated with Key from .env")

    except Exception as e:
        print(f"❌ Deployment failed: {e}")

if __name__ == "__main__":
    deploy()