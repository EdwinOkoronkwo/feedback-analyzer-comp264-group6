import os
from dotenv import load_dotenv

# Load the .env file
load_dotenv()

class Settings:
    PROJECT_NAME: str = "🛡️ AI Sentinel"
    
    # AWS Settings
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME")
    DYNAMODB_TABLE: str = os.getenv("DYNAMODB_TABLE", "FeedbackData")
    
    @classmethod
    def validate(cls):
        """Ensures all required settings are present."""
        if not cls.S3_BUCKET_NAME:
            raise ValueError("❌ S3_BUCKET_NAME is missing in .env file!")
        print(f"✅ Config Loaded: Using bucket {cls.S3_BUCKET_NAME}")

# Initialize and validate on import
settings = Settings()
settings.validate()