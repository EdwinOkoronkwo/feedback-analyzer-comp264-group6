from dotenv import load_dotenv

from chalicelib.utils.logger import FileAuditLogger
load_dotenv()

from chalicelib.persistence.dynamodb_storage import DynamoDBStorage

def test_database_persistence():
    logger = FileAuditLogger()
    storage = DynamoDBStorage(logger=logger, table_name="FeedbackData")
    
    test_data = {"text": "Persistence verification test", "sentiment": "NEUTRAL"}
    
    print("--- 💾 Starting Persistence Test ---")
    result = storage.save(test_data)
    
    if result["status"] == "success":
        print(f"✅ Save Confirmed!")
        print(f"📍 Table Name: {result['table']}")
        print(f"🆔 Generated ID: {result['id']}")
    else:
        print(f"❌ Failure: {result.get('message')}")

if __name__ == "__main__":
    test_database_persistence()