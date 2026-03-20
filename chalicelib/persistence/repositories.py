import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from boto3.dynamodb.conditions import Attr
from chalicelib.models.models import UserModel, MetadataModel, SummaryModel
from decimal import Decimal

class BaseRepository:
    def __init__(self, table_name: str, db_resource, logger=None):
        self.table = db_resource.Table(table_name)
        self.logger = logger

    def _log(self, message: str, level: str = "INFO"):
        if self.logger:
            self.logger.log_event("DATABASE", level, message)

class UserRepository(BaseRepository):
    def __init__(self, db_resource, logger=None):
        super().__init__("Users", db_resource, logger)

    def save(self, user: UserModel):
        try:
            self.table.put_item(Item={
                "username": user.username,
                "password_hash": user.password_hash,
                "role": user.role,
                "created_at": user.created_at
            })
            self._log(f"User {user.username} saved.")
        except Exception as e:
            self._log(f"Save failed: {str(e)}", "ERROR")
            raise e

    def get_by_username(self, username: str) -> Optional[UserModel]:
        response = self.table.get_item(Key={'username': username})
        item = response.get('Item')
        return UserModel.from_db(item) if item else None

    def get_all_users(self) -> list:
        """
        Scans the 'Users' table and returns a list of UserModel objects.
        """
        try:
            # 1. Physical Scan of DynamoDB
            response = self.table.scan()
            items = response.get('Items', [])
            
            # 2. Convert raw dictionaries into UserModels using your from_dict method
            return [UserModel.from_dict(item) for item in items]
            
        except Exception as e:
            self.logger.log_event("DB_SCAN_ERROR", "ERROR", f"Failed to fetch users: {str(e)}")
            return []

class MetadataRepository(BaseRepository):
    def __init__(self, db_resource, logger=None):
        super().__init__("Metadata", db_resource, logger)

    def save_metadata(self, metadata_dict: dict):
        self.table.put_item(Item=metadata_dict)
        self._log("Metadata saved.")

    def get_metadata(self, feedback_id: str) -> Optional[MetadataModel]:
        response = self.table.get_item(Key={'feedback_id': feedback_id})
        item = response.get('Item')
        return MetadataModel.from_db(item) if item else None

class SummaryRepository(BaseRepository):
    def __init__(self, db_resource, logger=None):
        # 🎯 THE FIX: Ensure this matches the 'Summaries' table exactly
        super().__init__("Summaries", db_resource, logger)

    def save_summary(self, summary_dict: dict):
        """Saves the AI-generated analysis."""
        self.table.put_item(Item=summary_dict)
        self._log(f"Summary saved for ID: {summary_dict.get('feedback_id')}")

    def get_summary(self, feedback_id: str) -> Optional[SummaryModel]:
        """
        🎯 THE HANDSHAKE: Retrieves the record by the Master ID.
        This is where the 'Record Not Found' error is currently happening.
        """
        # Search the 'Summaries' table for the ID (e.g., 'text_job_5a2d9c0b')
        response = self.table.get_item(Key={'feedback_id': feedback_id})
        item = response.get('Item')
        
        if not item:
            self._log(f"Lookup Failed: {feedback_id} not found in Summaries table.", "WARNING")
            return None
            
        return SummaryModel.from_db(item)

    def get_by_user(self, username: str) -> List[SummaryModel]:
        """Retrieves history for the specific user."""
        try:
            response = self.table.scan(
                FilterExpression=Attr('user_id').eq(username)
            )
            items = response.get('Items', [])
            return [SummaryModel.from_db(item) for item in items]
        except Exception as e:
            self._log(f"History scan failed: {str(e)}", "ERROR")
            return []

    # Inside your SummaryRepository class
    def get_all_feedback(self):
        """
        Fetches all records from the local Summaries table.
        """
        try:
            # Scan the local DynamoDB table
            response = self.table.scan()
            items = response.get('Items', [])
            
            # Sort by timestamp if it exists, newest first
            items.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            return items
        except Exception as e:
            print(f"❌ Error fetching history: {e}")
            return []