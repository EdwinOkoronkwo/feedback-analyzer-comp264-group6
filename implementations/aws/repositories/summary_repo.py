from ...shared.base_dynamo import BaseDynamoRepository
from chalicelib.models import SummaryModel

class AWSSummaryRepository(BaseDynamoRepository):
    def __init__(self, db_resource, logger=None):
        """
        AWS-specific Summary Repository.
        Points to the 'Summaries' table in the cloud.
        """
        super().__init__("Summaries", db_resource, logger)

    def save_summary(self, summary: SummaryModel):
        """
        Saves the processed AI summary to DynamoDB.
        Uses to_dict() to handle Enum-to-string conversion.
        """
        self.table.put_item(Item=summary.to_dict())
        self._log(f"AWS Cloud Summary for {summary.feedback_id} saved.")

    def get_summary(self, feedback_id: str):
        """Retrieves a summary and reconstructs the SummaryModel."""
        item = self.get_by_id({'feedback_id': feedback_id})
        return SummaryModel.from_db(item) if item else None