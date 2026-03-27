import pandas as pd
import boto3

class LocalAnalyticsProvider:
    def __init__(self):
        """
        Initializes the provider by connecting directly to the 
        local VMware DynamoDB instance.
        """
        # 1. Initialize the resource directly (replaces the old get_dynamodb_resource)
        self.dynamodb = boto3.resource(
            'dynamodb', 
            endpoint_url="http://localhost:8000", 
            region_name="us-east-1"
        )
        
        # 2. Connect to the table
        self.table = self.dynamodb.Table('Feedback_Master')

    def get_sentiment_summary(self):
        """
        Mimics Athena results by scanning the local DynamoDB table
        and grouping counts by sentiment using Pandas.
        """
        try:
            # 1. Pull all records from local DynamoDB
            response = self.table.scan()
            items = response.get('Items', [])
            
            if not items:
                return []

            # 2. Use Pandas to aggregate (simulating an Athena SQL Group By)
            df = pd.DataFrame(items)
            
            # Safety check: Ensure 'sentiment' column exists in the data
            if 'sentiment' not in df.columns:
                return []

            # Count occurrences of each sentiment
            summary = df['sentiment'].value_counts().reset_index()
            summary.columns = ['sentiment', 'total']
            
            # Return as a list of dicts to match the original Athena provider format
            return summary.to_dict('records')
            
        except Exception as e:
            # We use a standard print here for terminal debugging in VMware
            print(f"Analytics Scan Error: {e}")
            return []