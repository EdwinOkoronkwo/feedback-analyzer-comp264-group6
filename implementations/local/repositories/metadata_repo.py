from ...shared.base_dynamo import BaseDynamoRepository
from chalicelib.models import MetadataModel
class LocalMetadataRepository(BaseDynamoRepository):
    def __init__(self, db_resource, logger=None):
        # Change "Metadata" to "Feedback_Metadata"
        super().__init__("Feedback_Metadata", db_resource, logger)

    def save_metadata(self, metadata):
        """
        Saves metadata safely. 
        Works if 'metadata' is a Model object OR a pre-formatted dictionary.
        """
        # 1. Safe extraction of the dictionary
        item = metadata.to_dict() if hasattr(metadata, 'to_dict') else metadata
        
        # 2. Safe extraction of the ID for logging
        fid = metadata.feedback_id if hasattr(metadata, 'feedback_id') else item.get('feedback_id')

        # 3. Save to the actual DynamoDB table
        self.table.put_item(Item=item)
        self._log(f"Local Metadata {fid} saved.")

    def get_metadata(self, feedback_id: str):
        """Retrieves and maps to MetadataModel."""
        item = self.get_by_id({'feedback_id': feedback_id})
        return MetadataModel.from_db(item) if item else None