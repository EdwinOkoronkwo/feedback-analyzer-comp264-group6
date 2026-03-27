import boto3

# Set the region you were using (e.g., 'us-east-1')
REGION = 'us-east-1' 

def cleanup():
    print(f"--- Starting Cleanup in {REGION} ---")

    # 1. EC2 & Elastic IPs
    ec2 = boto3.client('ec2', region_name=REGION)
    instances = ec2.describe_instances(Filters=[{'Name': 'instance-state-name', 'Values': ['running', 'stopped']}])
    
    for reservation in instances['Reservations']:
        for inst in reservation['Instances']:
            print(f"Terminating Instance: {inst['InstanceId']}")
            ec2.terminate_instances(InstanceIds=[inst['InstanceId']])

    # 2. Bedrock Provisioned Throughput
    bedrock = boto3.client('bedrock', region_name=REGION)
    try:
        provisioned = bedrock.list_provisioned_model_throughputs()
        for p in provisioned.get('provisionedModelSummaries', []):
            print(f"Deleting Provisioned Model: {p['provisionedModelName']}")
            bedrock.delete_provisioned_model_throughput(provisionedModelId=p['provisionedModelArn'])
    except Exception as e:
        print(f"Bedrock check skipped or failed: {e}")

    # 3. OpenSearch Serverless (The "Hidden" Cost)
    oss = boto3.client('opensearchserverless', region_name=REGION)
    try:
        collections = oss.list_collections()
        for c in collections.get('collectionSummaries', []):
            print(f"Deleting OpenSearch Collection: {c['name']}")
            oss.delete_collection(id=c['id'])
    except Exception as e:
        print(f"OpenSearch Serverless check skipped: {e}")

    print("--- Cleanup Tasks Sent ---")

if __name__ == "__main__":
    cleanup()