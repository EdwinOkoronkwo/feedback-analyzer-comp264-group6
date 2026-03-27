import boto3
import logging
from botocore.exceptions import ClientError

# chalicelib/persistence/s3_repository.py

class S3Repository:
    def __init__(self, bucket_name: str, region: str = "us-east-1"):
        self.s3_client = boto3.client('s3', region_name=region)
        self.bucket_name = bucket_name
        self.logger = logging.getLogger(__name__)

    def upload_file(self, file_bytes: bytes, file_name: str, content_type: str, feedback_id: str) -> str:
        """
        Uploads file to S3 prefixed with the feedback_id.
        The Lambda will split the key by '_' to get the ID back.
        """
        try:
            # Format: feedback_id_originalfilename.jpg
            # Example: 550e8400-e29b-41d4-a716_myphoto.jpg
            unique_key = f"{feedback_id}_{file_name}"
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=unique_key,
                Body=file_bytes,
                ContentType=content_type
            )
            
            self.logger.info(f"✅ Uploaded {unique_key} to {self.bucket_name}")
            return unique_key
            
        except ClientError as e:
            self.logger.error(f"❌ S3 Upload Failed: {e}")
            raise e