import os
from dotenv import load_dotenv
from chalicelib.analytics.schema_manager import AthenaSchemaManager

load_dotenv()

def initialize():
    print("🏗️  Initializing Athena Database and Table...")
    manager = AthenaSchemaManager(database="feedback_analytics")
    try:
        manager.setup_environment()
        print("✅ Success! Database 'feedback_analytics' and table 'feedback_data' created.")
    except Exception as e:
        print(f"❌ Failed to setup schema: {e}")

if __name__ == "__main__":
    initialize()