import boto3
import json
import zipfile
import io
import time

# Config
ROLE_NAME = "LabelWorkerRole"
FUNCTION_NAME = "LabelWorker"
REGION = "us-east-1"

iam = boto3.client('iam')
lmb = boto3.client('lambda', region_name=REGION)

def get_or_create_role():
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]
    }
    try:
        role = iam.create_role(RoleName=ROLE_NAME, AssumeRolePolicyDocument=json.dumps(trust_policy))
        # Attach only what this worker needs
        policies = [
            "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
            "arn:aws:iam::aws:policy/AmazonRekognitionFullAccess",
            "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess",
            "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
        ]
        for policy in policies:
            iam.attach_role_policy(RoleName=ROLE_NAME, PolicyArn=policy)
        print(f"✅ Created Role: {ROLE_NAME}")
        return role['Role']['Arn']
    except iam.exceptions.EntityAlreadyExistsException:
        return iam.get_role(RoleName=ROLE_NAME)['Role']['Arn']

def deploy_lambda(role_arn):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        # Zip only the label worker handler
        z.write('lambda/label_worker/handler.py', 'handler.py')
    
    buf.seek(0)
    zip_bytes = buf.read()  # Store it here so we don't have to seek again

    try:
        lmb.create_function(
            FunctionName=FUNCTION_NAME,
            Runtime='python3.12',
            Role=role_arn,
            Handler='handler.lambda_handler',
            Code={'ZipFile': zip_bytes}, # Use the variable
            Timeout=15
        )
        print(f"✅ Created Lambda: {FUNCTION_NAME}")
    except lmb.exceptions.ResourceConflictException:
        # No need to seek(0) because we use the variable
        lmb.update_function_code(
            FunctionName=FUNCTION_NAME, 
            ZipFile=zip_bytes # Use the variable
        )
        print(f"🔄 Updated Lambda: {FUNCTION_NAME}")

if __name__ == "__main__":
    arn = get_or_create_role()
    print("⏳ Waiting for IAM propagation...")
    time.sleep(10)
    deploy_lambda(arn)