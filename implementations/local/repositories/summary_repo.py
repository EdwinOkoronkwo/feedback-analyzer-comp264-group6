from ...shared.base_dynamo import BaseDynamoRepository
from chalicelib.models import SummaryModel

class LocalSummaryRepository(BaseDynamoRepository):
    def __init__(self, db_resource, logger=None):
        # CHANGE "Summaries" TO "Analysis_Summaries"
        super().__init__("Analysis_Summaries", db_resource, logger)

    def get_all_feedback(self):
        """Scans local DynamoDB and returns items sorted by timestamp."""
        # Note: self.table is automatically set by the Base class using the name above
        response = self.table.scan()
        items = response.get('Items', [])
        # Professional tip: Use .get() with a default to prevent sorting crashes
        items.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return items

    def save_summary(self, summary_data):
        """
        Saves the summary. 
        Note: If summary is already a dict from DataConverter, use it directly.
        """
        item = summary_data.to_dict() if hasattr(summary_data, 'to_dict') else summary_data
        self.table.put_item(Item=item)
        self._log(f"Local Summary saved successfully.")

    def get_summary(self, feedback_id: str):
        """
        Retrieves a single summary by feedback_id and 
        maps it back to a SummaryModel object.
        """
        # 1. Use the base class helper to get the raw dict from DynamoDB
        # We assume 'feedback_id' is your Partition Key
        item = self.get_by_id({'feedback_id': feedback_id})
        
        if not item:
            return None
            
        # 2. Convert the DB dictionary back into a Python Model Object
        # This allows the Aggregator to use .sentiment, .status, etc.
        from chalicelib.models import SummaryModel
        return SummaryModel.from_db(item)