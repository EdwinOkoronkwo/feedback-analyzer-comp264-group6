# chalicelib/ingestion/web_ingestor.py


from chalicelib.interfaces.logger import ILogger
from ..interfaces.ingestion import IIngestor

class WebIngestor(IIngestor):
    def __init__(self, logger: ILogger):
        self.logger = logger

    def load(self, source_data: dict) -> dict:
        self.logger.log_event("INGESTION_INPUT", "DEBUG", f"Raw data head: {str(source_data)[:50]}...")
        
        data = {
            "text": source_data.get("text", ""),
            "metadata": source_data.get("metadata", {}),
            "timestamp": source_data.get("timestamp")
        }
        
        self.logger.log_event("INGESTION_COMPLETE", "SUCCESS", "Data mapped to internal schema")
        return data