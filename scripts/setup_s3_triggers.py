import boto3

BUCKET_NAME = "comp264-edwin-1772030214"
FUNCTION_NAME = "LabelWorker"

s3 = boto3.client('s3')
lmb = boto3.client('lambda')

def connect_trigger():
    # 1. Get Lambda ARN
    fn_arn = lmb.get_function(FunctionName=FUNCTION_NAME)['Configuration']['FunctionArn']
    
    # 2. Grant S3 permission to invoke Lambda
    try:
        lmb.add_permission(
            FunctionName=FUNCTION_NAME,
            StatementId='s3-invoke-labels',
            Action='lambda:InvokeFunction',
            Principal='s3.amazonaws.com',
            SourceArn=f"arn:aws:s3:::{BUCKET_NAME}"
        )
    except lmb.exceptions.ResourceConflictException:
        pass

    # 3. Configure Notification
    s3.put_bucket_notification_configuration(
        Bucket=BUCKET_NAME,
        NotificationConfiguration={
            'LambdaFunctionConfigurations': [
                {
                    'LambdaFunctionArn': fn_arn,
                    'Events': ['s3:ObjectCreated:*']
                }
            ]
        }
    )
    print(f"✅ S3 Trigger connected: {BUCKET_NAME} -> {FUNCTION_NAME}")

if __name__ == "__main__":
    connect_trigger()