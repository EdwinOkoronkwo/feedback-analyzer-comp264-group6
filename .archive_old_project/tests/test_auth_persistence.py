import boto3
import uuid
import datetime
import bcrypt  # <--- Essential for fixing 'Invalid salt'
from botocore.exceptions import ClientError

# --- 1. CONFIGURATION ---
DYNAMO_ARGS = {
    'endpoint_url': 'http://localhost:8000',
    'region_name': 'us-east-1',
    'aws_access_key_id': 'local',
    'aws_secret_access_key': 'local'
}

TABLE_USERS = "Users"

class AuthTestSystem:
    def __init__(self):
        self.db = boto3.resource('dynamodb', **DYNAMO_ARGS)
        self.users_table = self.db.Table(TABLE_USERS)

    def create_test_user(self, username, password):
        """Creates a user with a PROPER bcrypt hash for the app to use."""
        print(f"🔨 Creating user '{username}' with hashed password...")
        
        # 1. Generate the hash (This fixes 'Invalid salt')
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        try:
            self.users_table.put_item(Item={
                'username': username,
                'password_hash': hashed.decode('utf-8'), # Store as string
                'role': 'admin',
                'id': str(uuid.uuid4())[:8],
                'created_at': datetime.datetime.utcnow().isoformat()
            })
            print(f"✅ User '{username}' created successfully.")
        except ClientError as e:
            print(f"❌ Failed to create user: {e}")

# --- 2. EXECUTION ---
if __name__ == "__main__":
    tester = AuthTestSystem()
    
    # Run this to fix your local DB
    tester.create_test_user("admin", "pass")
    
    print("\n" + "="*40)
    print("🏁 LOCAL AUTH REPAIRED. Try logging in to Streamlit now.")