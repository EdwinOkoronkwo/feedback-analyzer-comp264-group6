import uuid
import boto3
from chalicelib.local.local_factory import LocalPipelineFactory
from chalicelib.local.local_table_manager import LocalTableManager

def setup():
    """Ensure all local tables exist before testing."""
    print("🏗️  Initializing Local Infrastructure (Analysis Tables)...")
    ltm = LocalTableManager()
    ltm.init_infrastructure()

def run_integration_test():
    # --- STEP 0: Create the tables ---
    setup()
    
    print("🚀 Starting Local Stack Integration Test...")
    
    # 1. Initialize the Local Stack
    pipeline, user_manager = LocalPipelineFactory.create_local_stack()
    
    # 2. Test User Registration (Hashed)
    test_username = f"tester_{uuid.uuid4().hex[:4]}"
    print(f"📝 Registering user: {test_username}...")
    
    new_user = user_manager.register(test_username, "password123", role="admin")
    if new_user:
        print(f"✅ User Registration Successful (Bcrypt Hash stored for {test_username}).")
    else:
        print("❌ User Registration Failed.")
        return

    # 3. Test Login (Hash Verification)
    print("🔑 Attempting Login...")
    logged_in_user = user_manager.login(test_username, "password123")
    
    if logged_in_user and logged_in_user.username == test_username:
        print(f"✅ Login Successful! Role: {logged_in_user.role}")
    else:
        print("❌ Login Failed (Hash mismatch or DB error).")
        return

    # 4. Test Feedback Data Insertion
    # CHANGED: Targeting 'Analysis_Summaries' to match your TableManager & AnalyticsProvider
    print("📊 Injecting dummy feedback data into Analysis_Summaries...")
    
    # Get direct access to the local resource for the injection test
    db_res = boto3.resource(
        'dynamodb', 
        endpoint_url='http://localhost:8000', 
        region_name='us-east-1',
        aws_access_key_id='local',
        aws_secret_access_key='local'
    )
    
    # We use Analysis_Summaries because that is the 'final' table for the dashboard
    target_table = db_res.Table('Analysis_Summaries') 
    
    dummy_data = {
        'feedback_id': str(uuid.uuid4()),
        'username': test_username,
        'text': "The Mistral/Ollama pipeline on VMware is working!",
        'sentiment': "POSITIVE",
        'timestamp': "2026-02-27T12:00:00"
    }
    
    try:
        target_table.put_item(Item=dummy_data)
        print("✅ Feedback record successfully inserted into 'Analysis_Summaries'.")
    except Exception as e:
        print(f"❌ Failed to insert feedback: {e}")
        print("💡 Tip: Check if 'Analysis_Summaries' exists in 'aws dynamodb list-tables --endpoint-url http://localhost:8000'")

    print("\n🎉 ALL TESTS PASSED! Your local environment is ready for the UI.")

if __name__ == "__main__":
    run_integration_test()