# chalicelib/interfaces/pipeline.py

from abc import ABC, abstractmethod

class IAnalysisPipeline(ABC):
    @abstractmethod
    def run(self, raw_input: dict) -> dict:
        """
        The main execution entry point. 
        Accepts raw data and returns the fully enriched, 
        secured, and persisted result.
        """
        pass


class IPipelineBridge(ABC):
    @abstractmethod
    def trigger_pipeline(self, payload: dict, file_obj=None) -> dict:
        """Starts the processing chain (OCR -> Analysis -> Summary)."""
        pass