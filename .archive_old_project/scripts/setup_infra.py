import boto3
import json
import time

# Initialize clients
iam = boto3.client('iam')
dynamodb = boto3.client('dynamodb')

ROLE_NAME = 'FeedbackAnalyzerRole'
BUCKET_NAME = 'comp264-edwin-1772030214'

def setup_iam():
    print(f"--- 🛡️ Configuring IAM Role: {ROLE_NAME} ---")
    
    # 1. Trust Relationship
    # Defines which services can "assume" this role to act on your behalf.
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {
                "Service": [
                    "lambda.amazonaws.com",
                    "textract.amazonaws.com",
                    "comprehend.amazonaws.com"
                ]
            },
            "Action": "sts:AssumeRole"
        }]
    }

    try:
        iam.update_assume_role_policy(
            RoleName=ROLE_NAME,
            PolicyDocument=json.dumps(trust_policy)
        )
        print("✅ Trust Relationship updated.")
    except Exception as e:
        print(f"❌ Error updating trust policy: {e}")

    # 2. Functional Permissions Policy
    # Defines exactly what the role is allowed to do.
    permissions_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "S3Access",
                "Effect": "Allow",
                "Action": ["s3:GetObject", "s3:PutObject", "s3:ListBucket"],
                "Resource": [f"arn:aws:s3:::{BUCKET_NAME}", f"arn:aws:s3:::{BUCKET_NAME}/*"]
            },
            {
                "Sid": "DynamoDBAccess",
                "Effect": "Allow",
                "Action": ["dynamodb:PutItem", "dynamodb:GetItem", "dynamodb:UpdateItem", "dynamodb:DescribeTable"],
                "Resource": [
                    "arn:aws:dynamodb:us-east-1:*:table/Analysis_OCR",
                    "arn:aws:dynamodb:us-east-1:*:table/Analysis_Summaries"
                ]
            },
            {
                "Sid": "AIServicesAndLogs",
                "Effect": "Allow",
                "Action": [
                    "textract:DetectDocumentText",
                    "comprehend:DetectSentiment",
                    "comprehend:DetectKeyPhrases",
                    "comprehend:DetectDominantLanguage",
                    "translate:TranslateText",      # 🎯 Added Translate
                    "polly:SynthesizeSpeech",       # 🎯 Polly Access
                    "lambda:InvokeFunction",
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                "Resource": "*"
            }
        ]
    }

    try:
        iam.put_role_policy(
            RoleName=ROLE_NAME,
            PolicyName='FeedbackPipelinePolicy',
            PolicyDocument=json.dumps(permissions_policy)
        )
        print("✅ Full Functional permissions attached (Translate, Polly, AI, Logs).")
    except Exception as e:
        print(f"❌ Error attaching permissions: {e}")

def create_table(table_name):
    print(f"--- 📊 Creating Table: {table_name} ---")
    try:
        dynamodb.create_table(
            TableName=table_name,
            KeySchema=[{'AttributeName': 'feedback_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'feedback_id', 'AttributeType': 'S'}],
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        print(f"⏳ Waiting for {table_name} to become active...")
        waiter = dynamodb.get_waiter('table_exists')
        waiter.wait(TableName=table_name)
        print(f"✅ Table {table_name} is ready.")
    except dynamodb.exceptions.ResourceInUseException:
        print(f"ℹ️ Table {table_name} already exists. Skipping.")

if __name__ == "__main__":
    setup_iam()
    create_table('Analysis_OCR')
    create_table('Analysis_Summaries')
    print("\n🚀 Infrastructure Setup Complete!")