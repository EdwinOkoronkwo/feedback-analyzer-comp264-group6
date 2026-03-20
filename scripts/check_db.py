import boto3
import pandas as pd
from botocore.exceptions import ClientError

def check_analysis_system():
    REGION = "us-east-1" 
    db = boto3.resource('dynamodb', region_name=REGION)
    
    # The three tables your pipeline needs
    tables_to_check = [
        'Analysis_Translations', 
        'Analysis_Summaries', 
        'Analysis_Labels'
    ]
    
    print(f"🚀 Scanning Analysis Tables in {REGION}...\n")
    
    for table_name in tables_to_check:
        print(f"--- Table: {table_name} ---")
        table = db.Table(table_name)
        
        try:
            response = table.scan()
            items = response.get('Items', [])
            
            if not items:
                print("📭 Empty.\n")
                continue

            df = pd.DataFrame(items)
            # Display relevant columns for each table
            cols = [c for c in ['feedback_id', 'summary_text', 'translated_text', 'labels'] if c in df.columns]
            print(df[cols].to_string(index=False))
            print("\n")

        except ClientError as e:
            print(f"❌ Table Error: {e.response['Error']['Message']}\n")

if __name__ == "__main__":
    check_analysis_system()