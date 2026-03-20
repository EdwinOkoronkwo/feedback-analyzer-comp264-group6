import os
import time
import boto3
import zipfile
import io
import json


class CloudWorkerManager:
    def __init__(self, region="us-east-1", role_arn=None):
        # FIX: Don't let a positional argument mistake 'region' for 'function_name'
        self.region = region
        self.role_arn = role_arn
        self.lmb = boto3.client('lambda', region_name=region)
        self.iam = boto3.client('iam')

    def get_or_create_role(self, role_name):
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]
        }
        
        # 1. Get or Create the Role
        try:
            role_arn = self.iam.get_role(RoleName=role_name)['Role']['Arn']
        except self.iam.exceptions.NoSuchEntityException:
            print(f"🆕 Creating IAM Role: {role_name}...")
            role = self.iam.create_role(
                RoleName=role_name, 
                AssumeRolePolicyDocument=json.dumps(trust_policy)
            )
            role_arn = role['Role']['Arn']

        # 2. ALWAYS sync policies to ensure Bedrock (and others) are present
        policies = [
            "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
            "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess",
            "arn:aws:iam::aws:policy/AmazonS3FullAccess", 
            "arn:aws:iam::aws:policy/AmazonTextractFullAccess",
            "arn:aws:iam::aws:policy/TranslateFullAccess",
            "arn:aws:iam::aws:policy/service-role/AWSLambdaDynamoDBExecutionRole",
            "arn:aws:iam::aws:policy/AmazonBedrockFullAccess" # <--- The Missing Key
        ]
        
        print(f"🔄 Syncing policies for {role_name}...")
        for p in policies:
            self.iam.attach_role_policy(RoleName=role_name, PolicyArn=p)
            
        return role_arn

    def add_s3_permission(self, bucket_name):
        try:
            self.lmb.add_permission(
                FunctionName=self.name, StatementId=f's3-{self.name}',
                Action='lambda:InvokeFunction', Principal='s3.amazonaws.com',
                SourceArn=f"arn:aws:s3:::{bucket_name}"
            )
        except self.lmb.exceptions.ResourceConflictException:
            pass

    
    def get_function_arn(self, name=None):
        # Use the name passed in, or fall back to the instance name
        target_name = name or self.name
        return self.lmb.get_function(FunctionName=target_name)['Configuration']['FunctionArn']

    def create_dynamodb_trigger(self, table_name, function_name):
        """Programmatically links a DynamoDB Stream to a Lambda function."""
        ddb = boto3.client('dynamodb', region_name=self.region)
        
        # 1. Ensure Stream is enabled on the table
        print(f"📡 Enabling Stream on {table_name}...")
        table_info = ddb.update_table(
            TableName=table_name,
            StreamSpecification={
                'StreamEnabled': True,
                'StreamViewType': 'NEW_IMAGE'
            }
        )
        stream_arn = table_info['TableDescription']['LatestStreamArn']

        # 2. Create the Event Source Mapping
        try:
            print(f"🔗 Linking Stream to {function_name}...")
            self.lmb.create_event_source_mapping(
                EventSourceArn=stream_arn,
                FunctionName=function_name,
                Enabled=True,
                BatchSize=1, # Process one feedback at a time for real-time feel
                StartingPosition='LATEST'
            )
            print("✅ Trigger Created Successfully.")
        except self.lmb.exceptions.ResourceConflictException:
            print("ℹ️ Trigger already exists, skipping...")

    def update_athena_schema(self, bucket_name, database="feedback_analytics"):
        """Programmatically repoints Athena to the live-data folder."""
        athena = boto3.client('athena', region_name=self.region)
        query = f"ALTER TABLE feedback_data SET LOCATION 's3://{bucket_name}/live-data/';"
        
        print(f"🔍 Updating Athena table location to s3://{bucket_name}/live-data/...")
        athena.start_query_execution(
            QueryString=query,
            QueryExecutionContext={'Database': database},
            ResultConfiguration={'OutputLocation': f's3://{bucket_name}/query-results/'}
        )