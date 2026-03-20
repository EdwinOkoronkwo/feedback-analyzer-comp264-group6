import boto3

from chalicelib.utils.logger import FileAuditLogger

class LocalTableManager:
    def __init__(self):
        # Force connection to Local DynamoDB
        self.db = boto3.client(
            'dynamodb', 
            endpoint_url='http://localhost:8000',
            region_name='us-east-1',
            aws_access_key_id='local',
            aws_secret_access_key='local'
        )
        self.logger = FileAuditLogger(name="LocalTableManager")

    def _create_table_safe(self, params):
        try:
            self.db.create_table(**params)
            print(f"✅ Created {params['TableName']}")
        except self.db.exceptions.ResourceInUseException:
            print(f"ℹ️ {params['TableName']} already exists.")

    def init_infrastructure(self):
        """Builds all analysis tables required by the AI workers"""
        tables = [
            {'TableName': 'Analysis_Labels', 'Key': 'feedback_id'},
            {'TableName': 'Analysis_OCR', 'Key': 'feedback_id'},
            {'TableName': 'Analysis_Speech', 'Key': 'feedback_id'},
            {'TableName': 'Analysis_Summaries', 'Key': 'feedback_id'},
            {'TableName': 'Users', 'Key': 'username'}
        ]
        
        for t in tables:
            self._create_table_safe({
                'TableName': t['TableName'],
                'KeySchema': [{'AttributeName': t['Key'], 'KeyType': 'HASH'}],
                'AttributeDefinitions': [{'AttributeName': t['Key'], 'AttributeType': 'S'}],
                'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
            })
        
        # Special case for Translations (Hash + Range key)
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
            'ProvisionedThroughput': {'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        })