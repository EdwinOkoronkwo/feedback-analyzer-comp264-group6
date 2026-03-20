import os
import uuid
import time
from chalicelib.persistence.s3_repository import S3Repository
from web.config import settings

def bulk_upload(folder_path):
    # Initialize Repo
    s3_repo = S3Repository(bucket_name=settings.S3_BUCKET_NAME)
    
    # Check if folder exists
    if not os.path.exists(folder_path):
        print(f"❌ Error: Folder '{folder_path}' not found.")
        return

    files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    if not files:
        print(f"ℹ️ No images found in {folder_path}")
        return

    print(f"🚀 Found {len(files)} images. Starting bulk upload to {settings.S3_BUCKET_NAME}...\n")

    for filename in files:
        file_path = os.path.join(folder_path, filename)
        mock_id = str(uuid.uuid4())
        
        try:
            with open(file_path, "rb") as f:
                file_bytes = f.read()
            
            # Determine content type basic check
            content_type = "image/jpeg" if filename.lower().endswith(('.jpg', '.jpeg')) else "image/png"

            # The Programmatic Upload
            s3_repo.upload_file(
                file_bytes=file_bytes,
                file_name=filename,
                content_type=content_type,
                feedback_id=mock_id
            )
            
            print(f"✅ Uploaded: {filename} | ID: {mock_id}")
            # Optional: tiny sleep to avoid hitting local network rate limits, 
            # though S3 handles this easily.
            time.sleep(0.5) 
            
        except Exception as e:
            print(f"❌ Failed to upload {filename}: {e}")

    print(f"\n🏁 All uploads complete. Go check the 'Analysis_Labels' DynamoDB table!")

if __name__ == "__main__":
    # Change this to your local folder path
    TEST_FOLDER = "tests/sample_images" 
    bulk_upload(TEST_FOLDER)