
# chalicelib/interfaces/persistence.py
from abc import ABC, abstractmethod

class IPersistence(ABC):
    @abstractmethod
    def save(self, data: dict) -> bool:
        """Saves the final object to the database/storage"""
        pass