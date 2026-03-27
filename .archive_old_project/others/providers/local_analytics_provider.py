import pandas as pd

from scripts.db_config import get_dynamodb_resource


class LocalAnalyticsProvider:
    def __init__(self):
        self.dynamodb = get_dynamodb_resource()
        self.table = self.dynamodb.Table('Feedback_Master')

    def get_sentiment_summary(self):
        """
        Mimics Athena results by scanning the local DynamoDB table
        and grouping counts by sentiment.
        """
        try:
            # 1. Pull all records from local DynamoDB
            response = self.table.scan()
            items = response.get('Items', [])
            
            if not items:
                return []

            # 2. Use Pandas to aggregate (just like Athena would)
            df = pd.DataFrame(items)
            
            # Ensure 'sentiment' column exists
            if 'sentiment' not in df.columns:
                return []

            # Count occurrences of each sentiment
            summary = df['sentiment'].value_counts().reset_index()
            summary.columns = ['sentiment', 'total']
            
            # Return as a list of dicts to match the original Athena provider format
            return summary.to_dict('records')
            
        except Exception as e:
            print(f"Analytics Scan Error: {e}")
            return []