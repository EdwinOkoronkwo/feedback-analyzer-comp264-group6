import boto3
import bcrypt  # <--- Add this
from botocore.exceptions import ClientError

# --- CONFIG ---
DYNAMO_ARGS = {
    'endpoint_url': 'http://localhost:8000',
    'region_name': 'us-east-1',
    'aws_access_key_id': 'local',
    'aws_secret_access_key': 'local'
}

def add_user(username, password, role="admin"):
    db = boto3.resource('dynamodb', **DYNAMO_ARGS)
    table = db.Table('Users')
    
    print(f"👤 Creating user: {username} with hashed password...")
    
    # 1. Create a secure Bcrypt hash (This fixes 'Invalid salt')
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    try:
        table.put_item(Item={
            'username': username,
            # decode('utf-8') saves it as a string in DynamoDB
            'password_hash': hashed_password.decode('utf-8'), 
            'role': role
        })
        print(f"✅ User '{username}' successfully added with a secure hash.")
    except ClientError as e:
        print(f"❌ Failed to add user: {e.response['Error']['Message']}")

if __name__ == "__main__":
    # This will now work perfectly with your login screen
    add_user("admin", "pass")