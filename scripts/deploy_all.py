import boto3
import zipfile
import os
import json
import time
from dotenv import load_dotenv
from botocore.exceptions import ClientError
import sys

# Adds the project root to the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.stepfn_deployer import StepFunctionDeployer

load_dotenv()

# --- CONFIGURATION ---
REGION = "us-east-1"
ROLE_NAME = "FeedbackAnalyzerRole"
BUCKET_NAME = "comp264-edwin-1772030214"
TABLE_NAME = "Analysis_Summaries"
REQUESTS_LAYER = 'arn:aws:lambda:us-east-1:770693421928:layer:Klayers-p39-requests:19'

WORKERS = [
    ("kag_worker", "lambda/kag_worker/aws_handler.py", "aws_handler.lambda_handler"),
    ("ocr_worker", "lambda/ocr_worker/aws_handler.py", "aws_handler.lambda_handler"),
    ("translate_worker", "lambda/translate_worker/aws_handler.py", "aws_handler.lambda_handler"),
    ("analysis_worker", "lambda/analysis_worker/aws_handler.py", "aws_handler.lambda_handler"),
    ("summary_worker", "lambda/summary_worker/aws_handler.py", "aws_handler.lambda_handler"),
    ("label_worker", "lambda/label_worker/aws_handler.py", "aws_handler.lambda_handler"),
    ("speech_worker", "lambda/speech_worker/aws_handler.py", "aws_handler.lambda_handler"),
    ("master_worker", "lambda/master_worker/aws_handler.py", "aws_handler.lambda_handler")
]

lambda_client = boto3.client('lambda', region_name=REGION)
sts_client = boto3.client('sts')

def create_zip(src, output_name):
    if not os.path.exists(src):
        print(f"⚠️  SKIPPING: {src} not found.")
        return None
    with zipfile.ZipFile(output_name, 'w') as z:
        z.write(src, 'aws_handler.py')
    with open(output_name, 'rb') as f:
        data = f.read()
    os.remove(output_name) 
    return data

def wait_for_lambda(name):
    waiter = lambda_client.get_waiter('function_updated_v2')
    waiter.wait(FunctionName=name)

def deploy():
    print("🏗️  Building Full Production Environment...")

    # 1. Dynamically get Account ID and Role ARN
    account_id = sts_client.get_caller_identity()['Account']
    role_arn = f"arn:aws:iam::{account_id}:role/{ROLE_NAME}"
    
    # 2. Worker Deployment Loop
    for name, src, handler in WORKERS:
        zip_bytes = create_zip(src, f"{name}.zip")
        if zip_bytes is None: continue
        
        layers = [REQUESTS_LAYER] if "summary" in name else []
        env_vars = {'Variables': {'SUMMARIES_TABLE': TABLE_NAME, 'S3_BUCKET_NAME': BUCKET_NAME}}

        try:
            print(f"📦 Deploying {name}...")
            lambda_client.create_function(
                FunctionName=name, Runtime='python3.9', Role=role_arn,
                Handler=handler, Code={'ZipFile': zip_bytes},
                Timeout=60, MemorySize=256, Environment=env_vars, Layers=layers
            )
        except ClientError:
            print(f"🔄 Updating {name}...")
            lambda_client.update_function_code(FunctionName=name, ZipFile=zip_bytes)
            time.sleep(2) 

    # 🎯 3. DEFINE ASL USING THE DISCOVERED ACCOUNT_ID
    print("\n🔗 Linking the 7-Step Pipeline...")
    
    asl_definition = {
        "StartAt": "KAG_Worker",
        "States": {
            "KAG_Worker": {"Type": "Task", "Resource": f"arn:aws:lambda:{REGION}:{account_id}:function:kag_worker", "Next": "OCR_Worker"},
            "OCR_Worker": {"Type": "Task", "Resource": f"arn:aws:lambda:{REGION}:{account_id}:function:ocr_worker", "Next": "Translate_Worker"},
            "Translate_Worker": {"Type": "Task", "Resource": f"arn:aws:lambda:{REGION}:{account_id}:function:translate_worker", "Next": "Analysis_Worker"},
            "Analysis_Worker": {"Type": "Task", "Resource": f"arn:aws:lambda:{REGION}:{account_id}:function:analysis_worker", "Next": "Summary_Worker"},
            "Summary_Worker": {"Type": "Task", "Resource": f"arn:aws:lambda:{REGION}:{account_id}:function:summary_worker", "Next": "Label_Worker"},
            "Label_Worker": {"Type": "Task", "Resource": f"arn:aws:lambda:{REGION}:{account_id}:function:label_worker", "Next": "Speech_Worker"},
            "Speech_Worker": {
                "Type": "Task", 
                "Resource": f"arn:aws:lambda:{REGION}:{account_id}:function:speech_worker", 
                "End": True 
            }
        }
    }

    # Use the helper to deploy the Step Function
    sfn_tool = StepFunctionDeployer(REGION, role_arn)
    # The helper should handle json.dumps() internally
    sfn_arn = sfn_tool.create_or_update_sfn("FeedbackOrchestrator", asl_definition)

    # 🎯 4. Bind Master Worker to SFN
    print(f"📡 Binding Master Worker to SFN...")
    wait_for_lambda("master_worker") 

    lambda_client.update_function_configuration(
        FunctionName="master_worker",
        Environment={
            'Variables': {
                'STATE_MACHINE_ARN': sfn_arn,
                'SUMMARIES_TABLE': TABLE_NAME,
                'S3_BUCKET_NAME': BUCKET_NAME
            }
        }
    )
    print("\n✨ SYSTEM ONLINE. Full Pipeline Active.")

if __name__ == "__main__":
    deploy()