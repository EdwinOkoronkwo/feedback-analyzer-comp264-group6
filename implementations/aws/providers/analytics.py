import boto3
import os
import time
from chalicelib.interfaces.analytics import IAnalyticsProvider

class AthenaAnalyticsProvider(IAnalyticsProvider):
    def __init__(self, region="us-east-1", workgroup="primary", database="default", s3_output=None):
        """
        Updated constructor to match the Factory's call.
        """
        # 1. Use the region passed from the Factory/Env
        self.client = boto3.client('athena', region_name=region)
        
        self.database = database
        self.workgroup = workgroup
        
        # 2. Setup the S3 output path
        bucket = os.environ.get('S3_BUCKET_NAME', 'comp264-edwin-1772030214')
        self.s3_output = s3_output or f"s3://{bucket}/athena-results/"

    def update_location(self):
        """Ensures Athena looks at the live-data folder."""
        # Logic to derive the live-data path from results path
        live_folder = self.s3_output.split('athena-results/')[0] + "live-data/"
        location_query = f"ALTER TABLE feedback_data SET LOCATION '{live_folder}'"
        
        try:
            self.client.start_query_execution(
                QueryString=location_query,
                QueryExecutionContext={'Database': self.database},
                ResultConfiguration={'OutputLocation': self.s3_output}
            )
        except Exception as e:
            print(f"⚠️ Athena Location Update Failed: {e}")

    def run_query(self, sql_query: str):
        response = self.client.start_query_execution(
            QueryString=sql_query,
            QueryExecutionContext={'Database': self.database},
            ResultConfiguration={'OutputLocation': self.s3_output}
        )
        query_id = response['QueryExecutionId']

        # Polling for completion
        while True:
            status = self.client.get_query_execution(QueryExecutionId=query_id)
            state = status['QueryExecution']['Status']['State']
            if state in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
                break
            time.sleep(1)

        if state != 'SUCCEEDED':
            raise Exception(f"Athena Query Failed: {state}")

        results = self.client.get_query_results(QueryExecutionId=query_id)
        return self._parse_results(results)

    def _parse_results(self, results):
        rows = results['ResultSet']['Rows']
        if not rows: return []
        headers = [col.get('VarCharValue', 'unknown') for col in rows[0]['Data']]
        return [
            dict(zip(headers, [col.get('VarCharValue', None) for col in row['Data']]))
            for row in rows[1:]
        ]

    def get_sentiment_summary(self):
        query = """
        SELECT 
            item.sentiment.s as sentiment, 
            count(*) as total 
        FROM feedback_data 
        WHERE item.sentiment.s IS NOT NULL
        GROUP BY item.sentiment.s
        """
        return self.run_query(query)