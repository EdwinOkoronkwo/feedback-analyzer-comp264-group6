import pandas as pd
import boto3

class LocalAnalyticsProvider:
    def __init__(self, table_name='Summaries'):
        # Initialize the local resource
        self.db = boto3.resource('dynamodb', 
                               endpoint_url='http://localhost:8000', 
                               region_name='us-east-1')
        self.table_name = table_name
        self.table = self.db.Table(self.table_name)

    def get_sentiment_summary(self):
        try:
            # 1. Scan the table
            response = self.table.scan()
            items = response.get('Items', [])
            
            if not items:
                print(f"🕵️ Analytics: Table '{self.table_name}' exists but is empty.")
                return []

            # 2. Process with Pandas
            df = pd.DataFrame(items)
            
            # 🎯 Column Normalization (Worker might use 'sentiment' or 'SentimentValue')
            col = 'sentiment' if 'sentiment' in df.columns else 'SentimentValue'
            
            if col not in df.columns:
                print(f"❌ Analytics: No sentiment column found. Available: {df.columns.tolist()}")
                return []

            # 3. Clean and Count
            # Convert to upper case to group 'Positive' and 'POSITIVE' together
            summary = df[col].astype(str).str.upper().value_counts().reset_index()
            summary.columns = ['sentiment', 'total']
            
            # Return as list of dicts: [{'sentiment': 'POSITIVE', 'total': 5}, ...]
            return summary.to_dict('records')

        except Exception as e:
            print(f"🚨 Analytics Provider Error: {e}")
            return []

    def update_location(self):
        """Mock for Athena compatibility"""
        pass