import boto3
import time
import getpass # To grab your local OS username automatically

def create_unique_bucket():
    s3 = boto3.client('s3', region_name='us-east-1')
    
    # Generate a unique name: comp264-edwin-2026-171500
    user_prefix = getpass.getuser().lower().replace(" ", "-")
    timestamp = int(time.time())
    bucket_name = f"comp264-{user_prefix}-{timestamp}"
    
    try:
        print(f"📦 Attempting to create bucket: {bucket_name}...")
        
        # In us-east-1, we don't need a LocationConstraint
        s3.create_bucket(Bucket=bucket_name)
        
        print(f"✅ Success! Bucket '{bucket_name}' is ready.")
        return bucket_name
        
    except Exception as e:
        print(f"❌ Failed to create bucket: {e}")
        return None

if __name__ == "__main__":
    bucket = create_unique_bucket()
    if bucket:
        print(f"🚀 Save this name for your .env or config: {bucket}")