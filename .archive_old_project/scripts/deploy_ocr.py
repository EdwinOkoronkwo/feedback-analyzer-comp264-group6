import boto3
import zipfile
import os

lambda_client = boto3.client('lambda', region_name='us-east-1')
s3_client = boto3.client('s3', region_name='us-east-1')

# --- CONFIGURATION ---
FUNCTION_NAME = 'ocr_worker'
SRC_FILE = 'lambda/ocr_worker/aws_handler.py'
# Ensure this matches your actual IAM Role Name
ROLE_NAME = 'FeedbackAnalyzerRole' 
BUCKET_NAME = 'comp264-edwin-1772030214'
# ---------------------

def deploy():
    # 1. Zip the file
    zip_path = 'ocr_worker.zip'
    with zipfile.ZipFile(zip_path, 'w') as z:
        z.write(SRC_FILE, 'aws_handler.py')

    with open(zip_path, 'rb') as f:
        zip_content = f.read()

    # 2. Get the Role ARN automatically
    iam = boto3.client('iam')
    role_arn = iam.get_role(RoleName=ROLE_NAME)['Role']['Arn']

    try:
        # Update code if exists
        response = lambda_client.update_function_code(FunctionName=FUNCTION_NAME, ZipFile=zip_content)
        function_arn = response['FunctionArn']
        print(f"✅ {FUNCTION_NAME} code updated.")
    except lambda_client.exceptions.ResourceNotFoundException:
        # Create if new
        response = lambda_client.create_function(
            FunctionName=FUNCTION_NAME,
            Runtime='python3.9',
            Role=role_arn,
            Handler='aws_handler.lambda_handler',
            Code={'ZipFile': zip_content},
            Timeout=30
        )
        function_arn = response['FunctionArn']
        print(f"✅ {FUNCTION_NAME} created.")

    # 3. S3 Permissions
    try:
        lambda_client.add_permission(
            FunctionName=FUNCTION_NAME,
            StatementId='s3-trigger-permission',
            Action='lambda:InvokeFunction',
            Principal='s3.amazonaws.com',
            SourceArn=f'arn:aws:s3:::{BUCKET_NAME}'
        )
    except lambda_client.exceptions.ResourceConflictException:
        pass

    # 4. Configure S3 Trigger (Using the dynamic function_arn)
    s3_client.put_bucket_notification_configuration(
        Bucket=BUCKET_NAME,
        NotificationConfiguration={
            'LambdaFunctionConfigurations': [{
                'LambdaFunctionArn': function_arn, # <--- No more hardcoding!
                'Events': ['s3:ObjectCreated:*'],
                'Filter': {'Key': {'FilterRules': [{'Name': 'prefix', 'Value': 'uploads/'}]}}
            }]
        }
    )
    print(f"✅ S3 Trigger linked to {BUCKET_NAME}/uploads/ using ARN: {function_arn}")

if __name__ == "__main__":
    deploy()