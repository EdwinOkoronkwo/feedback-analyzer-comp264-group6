import boto3
import requests

def inspect_worker_code(function_name):
    lmb = boto3.client('lambda', region_name='us-east-1')
    try:
        response = lmb.get_function(FunctionName=function_name)
        code_url = response['Code']['Location']
        print(f"📝 Code for {function_name} is available at a temporary URL.")
        print("💡 You can download the .zip of the code to see if it handles S3 uploads.")
        # Optional: In a real terminal, you'd curl this URL to inspect the python files.
    except Exception as e:
        print(f"❌ Could not inspect {function_name}: {e}")

if __name__ == "__main__":
    inspect_worker_code('MasterWorker')