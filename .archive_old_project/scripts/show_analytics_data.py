import os
from dotenv import load_dotenv

from chalicelib.analytics.athena_provider import AthenaAnalyticsProvider


load_dotenv()

def show_all_feedback():
    # 1. Initialize the provider
    # Ensure your .env has S3_BUCKET_NAME and the DB name is correct
    provider = AthenaAnalyticsProvider(database="feedback_analytics")
    
    print("🔍 Querying Athena for all feedback records...")
    
    # 2. SQL to flatten the DynamoDB JSON structure
    # Note: We access the 'item' struct defined in your SchemaManager
    sql = """
    SELECT 
        item.id.s as id, 
        item.sentiment.s as sentiment, 
        item.text.s as original_text,
        item.created_at.s as date
    FROM feedback_data 
    LIMIT 50;
    """
    
    try:
        results = provider.run_query(sql)
        
        if not results:
            print("📭 No data found. Is the S3 export finished?")
            return

        # 3. Print a formatted table
        header = f"{'DATE':<25} | {'SENTIMENT':<12} | {'TEXT'}"
        print("\n" + header)
        print("-" * len(header) * 2)
        
        for row in results:
            date = row.get('date', 'N/A')[:23] # Trim ISO string
            sentiment = row.get('sentiment', 'UNKNOWN')
            text = row.get('original_text', '')[:50] + "..." # Truncate long text
            
            print(f"{date:<25} | {sentiment:<12} | {text}")
            
        print(f"\n✅ Showed {len(results)} records.")

    except Exception as e:
        print(f"❌ Error fetching data: {e}")

if __name__ == "__main__":
    show_all_feedback()