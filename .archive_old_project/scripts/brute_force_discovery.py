import boto3

def brute_force_discovery():
    # Common regions where your lab or project might be deployed
    regions = ['us-east-1', 'us-east-2', 'us-west-2']
    
    print("🔭 Searching for any Lambda functions across regions...\n")
    
    for region in regions:
        print(f"--- Checking {region} ---")
        try:
            lmb = boto3.client('lambda', region_name=region)
            functions = lmb.list_functions()
            
            if not functions['Functions']:
                print("  (No functions found)")
                continue

            for f in functions['Functions']:
                print(f"  ✅ Found: {f['FunctionName']}")
                # Check for table name matches if they exist
                if 'feedback' in f['FunctionName'].lower():
                    print(f"     ⭐ POTENTIAL MATCH: {f['FunctionName']}")
                    
        except Exception as e:
            print(f"  ❌ Access denied or error in {region}")
        print("-" * 20)

if __name__ == "__main__":
    brute_force_discovery()