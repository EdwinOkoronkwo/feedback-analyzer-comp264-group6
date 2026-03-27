import boto3
import uuid
from datetime import datetime
from decimal import Decimal

class DynamoDBStorage:
    def __init__(self, logger, table_name="FeedbackData"):
        self.db = boto3.resource('dynamodb')
        self.table = self.db.Table(table_name)
        self.logger = logger

    def save(self, data: dict) -> dict:
        record_id = str(uuid.uuid4())
        try:
            # We specifically extract and convert scores to Decimal
            raw_scores = data.get('analysis', {}).get('scores', {})
            formatted_scores = {k: Decimal(str(v)) for k, v in raw_scores.items()}

            item = {
                'id': record_id,
                'created_at': datetime.utcnow().isoformat(),
                'text': data.get('text'),
                'safe_text': data.get('safe_text'),
                'translated_text': data.get('translated_text'),
                'sentiment': data.get('analysis', {}).get('sentiment'),
                'scores': formatted_scores
            }

            # 1. This sends data to AWS
            self.table.put_item(Item=item)
            
            # 2. This logs it locally
            self.logger.log_event("DB_SAVE", "SUCCESS", f"ID: {record_id}")
            
            # 3. This tells the UI we are done (NO MORE self.table_name)
            return {
                "status": "success", 
                "id": record_id, 
                "table": "FeedbackData"
            }
        except Exception as e:
            self.logger.log_event("DB_ERR", "ERROR", str(e))
            return {"status": "error", "message": str(e)}

    def save_user(self, user_data: dict):
        try:
            table = self.resource.Table('Users')
            table.put_item(Item=user_data)
            return True
        except Exception as e:
            self.logger.log_event("DB_USER_SAVE_ERR", "ERROR", str(e))
            return False

    def get_all_users(self) -> list:
        try:
            table = self.resource.Table('Users')
            response = table.scan()
            return response.get('Items', [])
        except Exception as e:
            self.logger.log_event("DB_USER_READ_ERR", "ERROR", str(e))
            return []

    def get_user_by_username(self, username: str):
        try:
            table = self.resource.Table('Users')
            response = table.get_item(Key={'username': username})
            return response.get('Item')
        except Exception as e:
            self.logger.log_event("DB_USER_FETCH_ERR", "ERROR", str(e))
            return None

    