import boto3
import os
import time
from chalicelib.interfaces.analytics import IAnalyticsProvider

class AthenaAnalyticsProvider(IAnalyticsProvider):
    def __init__(self, region="us-east-1", workgroup="primary", database="feedback_analytics", s3_output=None):
        self.client = boto3.client('athena', region_name=region)
        self.database = database
        self.workgroup = workgroup
        
        # Pull bucket from env or fallback to your specific bucket
        bucket = os.environ.get('S3_BUCKET_NAME', 'comp264-edwin-1772030214')
        self.s3_output = s3_output or f"s3://{bucket}/athena-results/"

    def wait_for_query(self, query_id):
        """Helper to poll Athena and catch specific error reasons."""
        while True:
            response = self.client.get_query_execution(QueryExecutionId=query_id)
            state = response['QueryExecution']['Status']['State']
            
            if state == 'SUCCEEDED':
                return True
            if state in ['FAILED', 'CANCELLED']:
                # 🎯 THE CRITICAL CHECK: Get the real reason from AWS
                reason = response['QueryExecution']['Status'].get('StateChangeReason', 'Unknown error')
                print(f"❌ Athena Query {query_id} {state}: {reason}")
                raise Exception(f"Athena Query {state}: {reason}")
            
            time.sleep(1)

    def update_location(self):
        """Ensures Athena looks at the live-data folder and waits for it to apply."""
        # Derive live-data path (assuming it's in the same bucket as results)
        base_s3 = self.s3_output.split('athena-results/')[0]
        live_folder = f"{base_s3}live-data/"
        
        # Note: If your table is partitioned, you should use MSCK REPAIR TABLE instead
        location_query = f"ALTER TABLE feedback_data SET LOCATION '{live_folder}'"
        
        try:
            print(f"🔄 Updating Athena table location to: {live_folder}")
            response = self.client.start_query_execution(
                QueryString=location_query,
                QueryExecutionContext={'Database': self.database},
                ResultConfiguration={'OutputLocation': self.s3_output}
            )
            self.wait_for_query(response['QueryExecutionId'])
            print("✅ Location update successful.")
        except Exception as e:
            print(f"⚠️ Athena Location Update Failed: {e}")

    def run_query(self, sql_query: str):
        """Runs query and returns parsed results with detailed error handling."""
        try:
            response = self.client.start_query_execution(
                QueryString=sql_query,
                QueryExecutionContext={'Database': self.database},
                ResultConfiguration={'OutputLocation': self.s3_output}
            )
            query_id = response['QueryExecutionId']
            
            # Wait for execution and handle failures
            self.wait_for_query(query_id)

            # Fetch and parse results
            results = self.client.get_query_results(QueryExecutionId=query_id)
            return self._parse_results(results)
            
        except Exception as e:
            # This will now include the specific "StateChangeReason"
            print(f"🔥 Query Error: {str(e)}")
            raise e

    def _parse_results(self, results):
        rows = results['ResultSet']['Rows']
        if not rows: return []
        
        headers = [col.get('VarCharValue', 'unknown') for col in rows[0]['Data']]
        return [
            dict(zip(headers, [col.get('VarCharValue', '0') for col in row['Data']]))
            for row in rows[1:]
        ]

    def get_sentiment_summary(self):
        # This query matches your schema: feedback_data table with nested 'item' structure
        query = """
        SELECT 
            item.sentiment.s as sentiment, 
            count(*) as total 
        FROM feedback_data 
        WHERE item.sentiment.s IS NOT NULL
        GROUP BY item.sentiment.s
        """
        return self.run_query(query)