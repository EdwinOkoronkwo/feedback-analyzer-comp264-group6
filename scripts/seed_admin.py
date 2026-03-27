import boto3
import bcrypt
import uuid
from datetime import datetime, UTC

# CONFIGURATION
TABLE_NAME = "Users"
ADMIN_USER = "admin"        # Updated
ADMIN_PASS = "password123"  # Updated

def seed():
    # Explicitly setting region to match your current setup
    db = boto3.resource('dynamodb', region_name='us-east-1')
    table = db.Table(TABLE_NAME)
    
    # Generate the Bcrypt hash that your UserManager expects
    hashed = bcrypt.hashpw(ADMIN_PASS.encode('utf-8'), bcrypt.gensalt())
    
    user_item = {
        "username": ADMIN_USER,
        "password_hash": hashed.decode('utf-8'),
        "id": str(uuid.uuid4()),
        "role": "admin",
        "created_at": datetime.now(UTC).isoformat()
    }
    
    print(f"Attempting to seed admin user: {ADMIN_USER}...")
    try:
        table.put_item(Item=user_item)
        print("✅ Success! You can now log in with 'admin' / 'password123'")
    except Exception as e:
        print(f"❌ Failed to seed user: {e}")

if __name__ == "__main__":
    seed()