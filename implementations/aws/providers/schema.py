import os
import boto3
import time

class AthenaSchemaManager:
    def __init__(self, database="feedback_analytics"):
        self.client = boto3.client('athena')
        self.database = database
        
        # 1. Use environment variable for the bucket name
        self.bucket = os.environ.get('S3_BUCKET_NAME', 'comp264-edwin-1772030214')
        
        # 2. Setup the paths
        self.s3_output = f"s3://{self.bucket}/athena-results/"
        self.live_data_location = f"s3://{self.bucket}/live-data/"
        
        # 3. Synchronize location on init
        self.update_location()

    def update_location(self):
        """Programmatically points the Athena table to the live-data folder."""
        query = f"ALTER TABLE feedback_data SET LOCATION '{self.live_data_location}';"
        
        try:
            self.client.start_query_execution(
                QueryString=query,
                QueryExecutionContext={'Database': self.database},
                ResultConfiguration={'OutputLocation': self.s3_output}
            )
            print(f"✅ Athena Schema: Table location updated to {self.live_data_location}")
        except Exception as e:
            print(f"ℹ️ Athena Schema: Table location update skipped (Table might not exist).")

    def setup_environment(self):
        """Orchestrates the creation of the cloud analytics environment."""
        print(f"🛠️ Setting up Athena environment for database: {self.database}")
        self._create_database()
        self._create_feedback_table()

    def _create_database(self):
        sql = f"CREATE DATABASE IF NOT EXISTS {self.database}"
        self._execute_ddl(sql)

    def _create_feedback_table(self):
        """Defines the external table structure for JSON data in S3."""
        sql = f"""
        CREATE EXTERNAL TABLE IF NOT EXISTS {self.database}.feedback_data (
          item struct<
            feedback_id:string,
            sentiment:struct<s:string>,
            summary:string,
            timestamp:string
          >
        )
        ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
        LOCATION '{self.live_data_location}';
        """
        self._execute_ddl(sql)

    def _execute_ddl(self, sql):
        response = self.client.start_query_execution(
            QueryString=sql,
            ResultConfiguration={'OutputLocation': self.s3_output}
        )
        query_id = response['QueryExecutionId']
        
        while True:
            status = self.client.get_query_execution(QueryExecutionId=query_id)
            state = status['QueryExecution']['Status']['State']
            if state in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
                break
            time.sleep(0.5)
        
        if state != 'SUCCEEDED':
            reason = status['QueryExecution']['Status'].get('StateChangeReason', 'Unknown error')
            raise Exception(f"DDL Failed: {reason}")
