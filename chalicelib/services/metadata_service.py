import bcrypt
from typing import Optional, Dict, Any

from chalicelib.models.feedback import MetadataModel
from chalicelib.utils.converters import DataConverter



class MetadataService:
    def __init__(self, repo):
        self.repo = repo

    def save_metadata(self, metadata):
        # This line makes it "AWS-Proof" and "Local-Proof"
        # It converts the object to a dict ONLY if it hasn't been converted yet.
        item = DataConverter.model_to_db_dict(metadata) if not isinstance(metadata, dict) else metadata
        
        return self.table.put_item(Item=item)
    def get_metadata(self, feedback_id: str) -> MetadataModel:
        meta = self.repo.get_metadata(feedback_id)
        if not meta:
            # Good practice to keep this specific for your Diploma error handling
            raise FileNotFoundError(f"Data Error: Metadata for ID {feedback_id} missing.")
        return meta

