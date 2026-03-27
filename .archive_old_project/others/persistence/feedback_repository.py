from decimal import Decimal
from chalicelib.models.feedback import FeedbackModel
from boto3.dynamodb.conditions import Attr, Key

class FeedbackRepository:
    # Changed default table_name to match LocalTableManager
    def __init__(self, db_resource, logger, table_name="Analysis_Summary"):
        self.table = db_resource.Table(table_name)
        self.logger = logger

    def save(self, feedback: FeedbackModel):
        item = feedback.to_dict()
        # Handle Decimal conversion for AWS compatibility
        if item.get('confidence_scores'):
            item['confidence_scores'] = {k: Decimal(str(v)) for k, v in item['confidence_scores'].items()}
        
        self.table.put_item(Item=item)
        self.logger.log_event("FEEDBACK_SAVE", "SUCCESS", f"ID: {feedback.id}")

    def get_final_result(self, feedback_id: str) -> FeedbackModel:
        try:
            # STOP: Don't split. Use the EXACT ID the worker used.
            response = self.table.get_item(Key={'feedback_id': feedback_id})
            item = response.get('Item')
            
            if item:
                return FeedbackModel.from_dict(item)
            
            # If not found, log it so we know WHY it's missing
            self.logger.log_event("DB_MISS", "WARN", f"ID {feedback_id} not found")
            return None
        except Exception as e:
            self.logger.log_event("DB_GET_ERR", "ERROR", str(e))
            return None

    def get_by_user(self, user_id: str):
        try:
            # We scan the table and check both common field names
            response = self.table.scan()
            items = response.get('Items', [])
            
            matching_items = []
            for item in items:
                # Check both 'user_id' and 'username' for a match
                db_user = item.get('user_id') or item.get('username')
                
                if db_user == user_id:
                    # Fix the 'summary_text' vs 'summary' mapping here too
                    if 'summary_text' in item:
                        item['summary'] = item['summary_text']
                    matching_items.append(FeedbackModel.from_dict(item))
                    
            return matching_items
        except Exception as e:
            self.logger.log_event("DB_QUERY_ERR", "ERROR", str(e))
            return []

    def get_all_feedback(self) -> list[FeedbackModel]:
        """Fetches every feedback record (Admin only)."""
        try:
            response = self.table.scan()
            items = response.get('Items', [])
            self.logger.log_event("DB_SCAN", "SUCCESS", f"Retrieved {len(items)} total records")
            return [FeedbackModel.from_dict(item) for item in items]
        except Exception as e:
            self.logger.log_event("DB_SCAN_ERR", "ERROR", str(e))
            return []




# from decimal import Decimal
# from chalicelib.models.feedback import FeedbackModel
# from boto3.dynamodb.conditions import Attr


# class FeedbackRepository:
#     def __init__(self, db_resource, logger, table_name="FeedbackData"):
#         self.table = db_resource.Table(table_name)
#         self.logger = logger

#     def save(self, feedback: FeedbackModel):
#         item = feedback.to_dict()
#         # Handle Decimal conversion for AWS compatibility
#         if item.get('confidence_scores'):
#             item['confidence_scores'] = {k: Decimal(str(v)) for k, v in item['confidence_scores'].items()}
        
#         self.table.put_item(Item=item)
#         self.logger.log_event("FEEDBACK_SAVE", "SUCCESS", f"ID: {feedback.id}")


#     def get_by_user(self, user_id: str) -> list[FeedbackModel]:
#         """Fetches feedback records only for the specified user."""
#         try:
#             # We use scan with a filter. For very large tables, 
#             # a Global Secondary Index (GSI) on user_id would be better.
#             response = self.table.scan(
#                 FilterExpression=Attr('user_id').eq(user_id)
#             )
#             items = response.get('Items', [])
            
#             self.logger.log_event("DB_QUERY", "SUCCESS", f"Found {len(items)} records for user {user_id}")
            
#             return [FeedbackModel.from_dict(item) for item in items]
            
#         except Exception as e:
#             self.logger.log_event("DB_QUERY_ERR", "ERROR", str(e))
#             return []

#     def get_all_feedback(self) -> list[FeedbackModel]:
#         """Fetches every feedback record in the system (Admin only)."""
#         try:
#             response = self.table.scan()
#             items = response.get('Items', [])
            
#             self.logger.log_event("DB_SCAN", "SUCCESS", f"Retrieved {len(items)} total records")
            
#             # Convert the raw DynamoDB dicts back into FeedbackModel objects
#             return [FeedbackModel.from_dict(item) for item in items]
            
#         except Exception as e:
#             self.logger.log_event("DB_SCAN_ERR", "ERROR", str(e))
#             return []