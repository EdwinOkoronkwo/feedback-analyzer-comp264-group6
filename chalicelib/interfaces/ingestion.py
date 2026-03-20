# chalicelib/interfaces/ingestion.py

from abc import ABC, abstractmethod

class IIngestor(ABC):
    @abstractmethod
    def load(self, source_data: dict) -> dict:
        """Standardizes raw input into a internal dictionary format"""
        pass