import boto3
import json
import time

class CloudWorkerManager:
    def __init__(self, region="us-east-1", role_arn=None):
        self.region = region
        self.role_arn = role_arn
        self.lmb = boto3.client('lambda', region_name=region)
        self.iam = boto3.client('iam')

    def get_or_create_role(self, role_name):
        """Ensures the Lambda role exists and has all required AI/DB permissions."""
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]
        }
        
        try:
            role_arn = self.iam.get_role(RoleName=role_name)['Role']['Arn']
        except self.iam.exceptions.NoSuchEntityException:
            print(f"🆕 Creating IAM Role: {role_name}...")
            role = self.iam.create_role(
                RoleName=role_name, 
                AssumeRolePolicyDocument=json.dumps(trust_policy)
            )
            role_arn = role['Role']['Arn']

        # Essential policies for a Multi-Agent AI system
        policies = [
            "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
            "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess",
            "arn:aws:iam::aws:policy/AmazonS3FullAccess", 
            "arn:aws:iam::aws:policy/AmazonTextractFullAccess",
            "arn:aws:iam::aws:policy/TranslateFullAccess",
            "arn:aws:iam::aws:policy/AmazonBedrockFullAccess" # Required for Mistral/Claude on AWS
        ]
        
        print(f"🔄 Syncing policies for {role_name}...")
        for p in policies:
            self.iam.attach_role_policy(RoleName=role_name, PolicyArn=p)
            
        return role_arn

    def add_s3_permission(self, function_name, bucket_name):
        """Allows S3 to trigger a specific Lambda function."""
        try:
            self.lmb.add_permission(
                FunctionName=function_name, 
                StatementId=f's3-trigger-{function_name}',
                Action='lambda:InvokeFunction', 
                Principal='s3.amazonaws.com',
                SourceArn=f"arn:aws:s3:::{bucket_name}"
            )
        except self.lmb.exceptions.ResourceConflictException:
            pass

    def create_dynamodb_trigger(self, table_name, function_name):
        """Links a DynamoDB Stream (New Image) to a worker."""
        ddb = boto3.client('dynamodb', region_name=self.region)
        
        print(f"📡 Enabling Stream on {table_name}...")
        table_info = ddb.update_table(
            TableName=table_name,
            StreamSpecification={'StreamEnabled': True, 'StreamViewType': 'NEW_IMAGE'}
        )
        # Wait a moment for stream to initialize
        time.sleep(2) 
        stream_arn = ddb.describe_table(TableName=table_name)['Table']['LatestStreamArn']

        try:
            print(f"🔗 Linking Stream to {function_name}...")
            self.lmb.create_event_source_mapping(
                EventSourceArn=stream_arn,
                FunctionName=function_name,
                Enabled=True,
                BatchSize=1,
                StartingPosition='LATEST'
            )
        except self.lmb.exceptions.ResourceConflictException:
            print(f"ℹ️ Trigger already exists for {function_name}")