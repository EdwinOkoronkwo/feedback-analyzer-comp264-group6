import os
import boto3
import time

class AthenaSchemaManager:
    def __init__(self, database="feedback_analytics"):
        self.client = boto3.client('athena')
        self.database = database
        
        # 1. Properly define the bucket first so all methods can see it
        self.bucket = os.environ.get('S3_BUCKET_NAME', 'comp264-edwin-1772030214')
        
        # 2. Setup the paths
        self.s3_output = f"s3://{self.bucket}/athena-results/"
        self.live_data_location = f"s3://{self.bucket}/live-data/"
        
        # 3. Update the location now that self.bucket is safe to use
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
            # If the table doesn't exist yet, ALTER will fail, which is fine
            print(f"ℹ️ Athena Schema: Table location not updated (Table might not exist yet).")

    def _create_feedback_table(self):
        """
        Modified to use the LIVE folder as the default location.
        Also matches the structure written by your Stream Lambda.
        """
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

    def setup_environment(self):
        """Creates the database and table if they don't exist."""
        print(f"🛠️ Setting up Athena environment for database: {self.database}")
        self._create_database()
        self._create_feedback_table()

    def _execute_ddl(self, sql):
        response = self.client.start_query_execution(
            QueryString=sql,
            ResultConfiguration={'OutputLocation': self.s3_output}
        )
        query_id = response['QueryExecutionId']
        
        # Wait for DDL to finish
        while True:
            status = self.client.get_query_execution(QueryExecutionId=query_id)
            state = status['QueryExecution']['Status']['State']
            if state in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
                break
            time.sleep(0.5)
        
        if state != 'SUCCEEDED':
            reason = status['QueryExecution']['Status'].get('StateChangeReason', 'Unknown error')
            raise Exception(f"DDL Failed: {reason}")

    def _create_database(self):
        sql = f"CREATE DATABASE IF NOT EXISTS {self.database}"
        self._execute_ddl(sql)

    

    
    def get_latest_export_s3_path(self):
        """Helper to find the most recent DynamoDB export folder in S3"""
        s3 = boto3.client('s3')
        bucket = os.environ.get('S3_BUCKET_NAME')
        prefix = "exports/AWSDynamoDB/"
        
        # List the export attempt folders
        response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix, Delimiter='/')
        
        if 'CommonPrefixes' not in response:
            raise Exception("No exports found in S3. Check if the export finished.")
            
        # Get the most recent one (sorted by folder name/timestamp)
        latest_folder = sorted([p['Prefix'] for p in response['CommonPrefixes']])[-1]
        
        # Athena needs the /data/ subfolder where the actual JSON lives
        return f"s3://{bucket}/{latest_folder}data/"

    