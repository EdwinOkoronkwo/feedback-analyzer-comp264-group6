import boto3
import os

# Set this in your terminal: export STAGE='LOCAL'
# If not set, it defaults to 'LOCAL'
STAGE = os.getenv('STAGE', 'LOCAL')

def get_dynamodb_resource():
    if STAGE == 'LOCAL':
        # Points to your local JAR service
        return boto3.resource('dynamodb', endpoint_url="http://localhost:8000", region_name="us-east-1")
    else:
        # Points to the actual AWS Cloud
        return boto3.resource('dynamodb', region_name="us-east-1")