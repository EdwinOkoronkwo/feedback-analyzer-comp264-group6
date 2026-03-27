import boto3
import zipfile
import io

lambda_client = boto3.client('lambda')
ddb_client = boto3.client('dynamodb')

def setup_automation():
    # 1. Enable DynamoDB Stream
    print("Enabling DynamoDB Stream...")
    table_desc = ddb_client.update_table(
        TableName='Analysis_Summaries',
        StreamSpecification={
            'StreamEnabled': True,
            'StreamViewType': 'NEW_IMAGE'
        }
    )
    stream_arn = table_desc['TableDescription']['LatestStreamArn']
    
    # 2. Package Lambda (Handler)
    # (Simplified: In a real env, you'd zip the lambdas/ folder)
    
    # 3. Create Event Source Mapping
    print(f"Connecting Stream {stream_arn} to Lambda...")
    lambda_client.create_event_source_mapping(
        EventSourceArn=stream_arn,
        FunctionName='AnalysisWorkerLambda', # Ensure this matches your created Lambda
        StartingPosition='LATEST',
        BatchSize=1
    )
    print("✅ Automation Bridge Established.")

if __name__ == "__main__":
    setup_automation()