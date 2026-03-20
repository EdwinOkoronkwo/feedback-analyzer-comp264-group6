import boto3
import uuid
import os

class BulkUploader:
    def __init__(self, bucket_name):
        self.bucket = bucket_name
        self.s3 = boto3.client('s3')

    def upload_samples(self, directory='tests/samples'):
        if not os.path.exists(directory):
            print(f"❌ Directory {directory} not found.")
            return

        print(f"🚀 Starting bulk upload to {self.bucket}...")
        for filename in os.listdir(directory):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                feedback_id = str(uuid.uuid4())
                self.s3.upload_file(
                    os.path.join(directory, filename), 
                    self.bucket, 
                    filename,
                    ExtraArgs={'Metadata': {'feedback_id': feedback_id}}
                )
                print(f"✅ Uploaded: {filename} | ID: {feedback_id}")