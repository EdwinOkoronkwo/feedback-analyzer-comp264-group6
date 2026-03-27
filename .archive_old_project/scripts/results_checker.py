import boto3
import pandas as pd

def check_all_results():
    db = boto3.resource('dynamodb', region_name='us-east-1')
    
    # List of all our project tables
    tables = [
        'Analysis_Labels', 
        'Analysis_OCR', 
        'Analysis_Translations', 
        'Analysis_Summaries'
    ]
    
    print("\n" + "="*50)
    print("🚀 AI FEEDBACK PIPELINE: RESULTS CHECKER")
    print("="*50)

    for table_name in tables:
        print(f"\n📊 Table: {table_name}")
        table = db.Table(table_name)
        
        try:
            response = table.scan()
            items = response.get('Items', [])
            
            if not items:
                print("   ℹ️ No records found.")
                continue
                
            # Convert to DataFrame for a clean table look
            df = pd.DataFrame(items)
            
            # Put feedback_id at the front for readability
            if 'feedback_id' in df.columns:
                cols = ['feedback_id'] + [c for c in df.columns if c != 'feedback_id']
                df = df[cols]
                
            print(df.to_string(index=False))
            
        except Exception as e:
            print(f"   ❌ Error reading table: {str(e)}")

    print("\n" + "="*50)
    print("✅ Check Complete.")

if __name__ == "__main__":
    check_all_results()