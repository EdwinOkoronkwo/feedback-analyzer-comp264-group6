# chalicelib/interfaces/security.py

from abc import ABC, abstractmethod

class ISecurity(ABC):
    @abstractmethod
    def mask_sensitive_info(self, text: str) -> str:
        """Identifies and masks PII (emails, passwords, IDs)"""
        pass