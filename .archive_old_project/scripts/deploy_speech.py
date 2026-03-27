import boto3
import zipfile

lambda_client = boto3.client('lambda', region_name='us-east-1')
iam = boto3.client('iam')

FUNCTION_NAME = 'speech_worker'
SRC_FILE = 'lambda/speech_worker/aws_handler.py'
ROLE_NAME = 'FeedbackAnalyzerRole'

def deploy():
    zip_path = 'speech_worker.zip'
    with zipfile.ZipFile(zip_path, 'w') as z:
        # Renames the file to 'aws_handler.py' inside the zip
        z.write(SRC_FILE, 'aws_handler.py')

    with open(zip_path, 'rb') as f:
        zip_content = f.read()

    role_arn = iam.get_role(RoleName=ROLE_NAME)['Role']['Arn']

    try:
        # Update existing function code
        lambda_client.update_function_code(FunctionName=FUNCTION_NAME, ZipFile=zip_content)
        print(f"✅ {FUNCTION_NAME} code updated.")
    except lambda_client.exceptions.ResourceNotFoundException:
        # Create new function with handler set to 'aws_handler.lambda_handler'
        lambda_client.create_function(
            FunctionName=FUNCTION_NAME,
            Runtime='python3.9',
            Role=role_arn,
            Handler='aws_handler.lambda_handler',
            Code={'ZipFile': zip_content},
            Timeout=30
        )
        print(f"✅ {FUNCTION_NAME} created.")

if __name__ == "__main__":
    deploy()