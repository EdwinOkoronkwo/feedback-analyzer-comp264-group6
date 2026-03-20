import os
import uuid
from chalicelib.persistence.s3_repository import S3Repository
from web.config import settings

def test_upload(file_path):
    # 1. Initialize the Repo (using your .env settings)
    s3_repo = S3Repository(bucket_name=settings.S3_BUCKET_NAME)
    
    # 2. Simulate a Feedback ID (just like the Pipeline does)
    mock_feedback_id = str(uuid.uuid4())
    
    # 3. Read the local file
    file_name = os.path.basename(file_path)
    try:
        with open(file_path, "rb") as f:
            file_bytes = f.read()
            
        print(f"📂 Loading: {file_name}")
        print(f"🆔 Mock ID: {mock_feedback_id}")

        # 4. Programmatic Upload
        # This is the exact same call your Streamlit app uses
        s3_repo.upload_file(
            file_bytes=file_bytes,
            file_name=file_name,
            content_type="image/jpeg",
            feedback_id=mock_feedback_id
        )

        print(f"🚀 Success! Check DynamoDB for feedback_id: {mock_feedback_id}")
        
    except FileNotFoundError:
        print(f"❌ Error: Could not find file at {file_path}")
    except Exception as e:
        print(f"❌ Upload failed: {e}")

if __name__ == "__main__":
    # Point this to a real image on your computer
    IMAGE_TO_TEST = "tests/sample_images/coffee.jpg" 
    test_upload(IMAGE_TO_TEST)