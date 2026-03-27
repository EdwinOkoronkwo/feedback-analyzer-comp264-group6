import boto3

def verify_lambda_trigger():
    lmb = boto3.client('lambda', region_name='us-east-1')
    FUNCTION_NAME = 'analysis_worker' # Ensure this matches your Lambda name
    
    print(f"🔎 Inspecting triggers for {FUNCTION_NAME}...")
    try:
        response = lmb.list_event_source_mappings(FunctionName=FUNCTION_NAME)
        mappings = response.get('EventSourceMappings', [])
        
        if not mappings:
            print("❌ ERROR: No DynamoDB trigger found. The Lambda is not 'listening' to the table.")
            return

        for m in mappings:
            print(f"📍 Source Table ARN: {m['EventSourceArn']}")
            print(f"🚦 Status: {m['State']}")
            print(f"✅ Enabled: {m['Enabled']}")
            
            if m['State'] != 'Enabled':
                print("💡 ACTION: You need to enable this mapping via CLI or Console.")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    verify_lambda_trigger()