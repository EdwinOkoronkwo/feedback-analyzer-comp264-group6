import boto3
import json

import boto3
import json

def sync_s3_triggers(bucket_name, lambda_arns):
    events = boto3.client('events')
    s3 = boto3.client('s3')
    sts = boto3.client('sts') # New client to get Account ID
    
    # 1. Get the real Account ID and Region
    account_id = sts.get_caller_identity()["Account"]
    region = boto3.session.Session().region_name
    
    # 2. Enable S3 EventBridge Notifications
    s3.put_bucket_notification_configuration(
        Bucket=bucket_name,
        NotificationConfiguration={'EventBridgeConfiguration': {}}
    )

    # 3. Create the Rule
    rule_name = f"{bucket_name}-fanout-rule"
    rule_arn = f"arn:aws:events:{region}:{account_id}:rule/{rule_name}" # FULLY QUALIFIED
    
    events.put_rule(
        Name=rule_name,
        EventPattern=json.dumps({
            "source": ["aws.s3"],
            "detail-type": ["Object Created"],
            "detail": {"bucket": {"name": [bucket_name]}}
        }),
        State='ENABLED'
    )

    # 4. Attach Targets
    targets = [{'Id': f"worker-{i}", 'Arn': arn} for i, arn in enumerate(lambda_arns)]
    events.put_targets(Rule=rule_name, Targets=targets)
    
    # 5. Add Permissions (With the correct, specific ARN)
    lmb = boto3.client('lambda')
    for arn in lambda_arns:
        func_name = arn.split(':')[-1]
        try:
            lmb.add_permission(
                FunctionName=func_name,
                StatementId=f'eb-{func_name}',
                Action='lambda:InvokeFunction',
                Principal='events.amazonaws.com',
                SourceArn=rule_arn # No more asterisks!
            )
        except lmb.exceptions.ResourceConflictException:
            pass
            
    print(f"✅ EventBridge Fan-out configured for {len(lambda_arns)} workers.")


def wire_dynamo_to_lambda(lambda_name, stream_arn):
    lmb = boto3.client('lambda')
    
    try:
        lmb.create_event_source_mapping(
            EventSourceArn=stream_arn,
            FunctionName=lambda_name,
            Enabled=True,
            BatchSize=1, # Process one image translation at a time
            StartingPosition='LATEST'
        )
        print(f"🔗 Linked {lambda_name} to DynamoDB Stream.")
    except lmb.exceptions.ResourceConflictException:
        print(f"ℹ️ {lambda_name} already linked to stream.")