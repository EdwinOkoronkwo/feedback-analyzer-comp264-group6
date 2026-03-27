import boto3
from chalicelib.utils.logger import FileAuditLogger

import boto3
from chalicelib.utils.logger import FileAuditLogger

class TableManager:
    def __init__(self, region="us-east-1"):
        self.db = boto3.client('dynamodb', region_name=region)
        self.logger = FileAuditLogger(name="TableManager")

    def _create_table_safe(self, params):
        """Helper to handle the 'Already Exists' logic for any table."""
        name = params['TableName']
        try:
            self.db.create_table(**params)
            print(f"⏳ Creating {name}...")
        except self.db.exceptions.ResourceInUseException:
            print(f"ℹ️ {name} already exists.")

    def create_labels_table(self):
        self._create_table_safe({
            'TableName': 'Analysis_Labels',
            'KeySchema': [{'AttributeName': 'feedback_id', 'KeyType': 'HASH'}],
            'AttributeDefinitions': [{'AttributeName': 'feedback_id', 'AttributeType': 'S'}],
            'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        })

    def create_ocr_table(self):
        # We add the STREAM here for the Translate pipeline
        self._create_table_safe({
            'TableName': 'Analysis_OCR',
            'KeySchema': [{'AttributeName': 'feedback_id', 'KeyType': 'HASH'}],
            'AttributeDefinitions': [{'AttributeName': 'feedback_id', 'AttributeType': 'S'}],
            'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5},
            'StreamSpecification': {
                'StreamEnabled': True,
                'StreamViewType': 'NEW_IMAGE'
            }
        })

    def create_translations_table(self):
        """Updated to include STREAMS for Speech and Summary workers."""
        self._create_table_safe({
            'TableName': 'Analysis_Translations',
            'KeySchema': [
                {'AttributeName': 'feedback_id', 'KeyType': 'HASH'},
                {'AttributeName': 'language', 'KeyType': 'RANGE'}
            ],
            'AttributeDefinitions': [
                {'AttributeName': 'feedback_id', 'AttributeType': 'S'},
                {'AttributeName': 'language', 'AttributeType': 'S'}
            ],
            'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5},
            # FIX: Enable stream so the AI chain continues
            'StreamSpecification': {
                'StreamEnabled': True,
                'StreamViewType': 'NEW_IMAGE'
            }
        })

    def create_speech_table(self):
        self._create_table_safe({
            'TableName': 'Analysis_Speech',
            'KeySchema': [{'AttributeName': 'feedback_id', 'KeyType': 'HASH'}],
            'AttributeDefinitions': [{'AttributeName': 'feedback_id', 'AttributeType': 'S'}],
            'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        })

    

    def get_stream_arn(self, table_name):
        """Retrieves the latest Stream ARN for a specific table."""
        try:
            response = self.db.describe_table(TableName=table_name)
            stream_arn = response['Table'].get('LatestStreamArn')
            if not stream_arn:
                self.logger.log_event("STREAM_NOT_FOUND", "WARNING", f"No stream enabled for {table_name}")
                return None
            return stream_arn
        except self.db.exceptions.ResourceNotFoundException:
            print(f"❌ Table {table_name} does not exist.")
            return None

    def create_summaries_table(self):
        """New table for Bedrock LLM outputs."""
        self._create_table_safe({
            'TableName': 'Analysis_Summaries',
            'KeySchema': [{'AttributeName': 'feedback_id', 'KeyType': 'HASH'}],
            'AttributeDefinitions': [{'AttributeName': 'feedback_id', 'AttributeType': 'S'}],
            'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        })

    def create_all_tables(self):
        self.logger.log_event("TABLE_CHECK", "INFO", "Deploying individual table schemas...")
        self.create_labels_table()
        self.create_ocr_table()
        self.create_translations_table()
        self.create_speech_table()
        self.create_summaries_table() # Add this

    