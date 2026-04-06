import boto3
import bcrypt

# 1. Setup Connection with "standard format" dummy credentials
# Some versions of Boto3 validate the length of the Access Key ID
db = boto3.resource('dynamodb', 
    endpoint_url='http://localhost:8000', 
    region_name='us-east-1',
    aws_access_key_id='AKIAEXAMPLE123456789',  # 🎯 20 characters long
    aws_secret_access_key='wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY' # 🎯 40 characters
)

table = db.Table('Users')

# 2. Configuration
NEW_USERNAME = "admin"
NEW_PASSWORD = "password123"

print(f"🔄 Resetting user to {NEW_USERNAME}...")

try:
    # 3. Generate the hash
    password_bytes = NEW_PASSWORD.encode('utf-8')
    salt = bcrypt.gensalt(rounds=12)
    hashed_pw = bcrypt.hashpw(password_bytes, salt).decode('utf-8')

    # 4. Add the new admin user
    table.put_item(Item={
        'username': NEW_USERNAME,
        'password_hash': hashed_pw,
        'role': 'admin',
        'created_at': '2026-04-05T15:15:00'
    })
    
    # 5. Clean up old user
    table.delete_item(Key={'username': 'analyst_edwin'})
    
    print("✅ Success! Login with:")
    print(f"Username: {NEW_USERNAME} | Password: {NEW_PASSWORD}")

except Exception as e:
    print(f"❌ Failed to reset user: {e}")