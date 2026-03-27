from ...shared.base_dynamo import BaseDynamoRepository
from chalicelib.models import MetadataModel

class AWSMetadataRepository(BaseDynamoRepository):
    def __init__(self, db_resource, logger=None):
        super().__init__("Metadata", db_resource, logger)

    def save_metadata(self, metadata: MetadataModel):
        """Saves metadata to AWS DynamoDB."""
        self.table.put_item(Item=metadata.to_dict())
        self._log(f"AWS Cloud Metadata {metadata.feedback_id} saved.")

    def get_metadata(self, feedback_id: str):
        """Retrieves metadata and maps to MetadataModel."""
        item = self.get_by_id({'feedback_id': feedback_id})
        return MetadataModel.from_db(item) if item else None