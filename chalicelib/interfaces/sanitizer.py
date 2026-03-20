# chalicelib/interfaces/sanitizer.py

from abc import ABC, abstractmethod

class ISanitizer(ABC):
    @abstractmethod
    def clean(self, text: str) -> str:
        """Removes noise, HTML, or unwanted characters from text"""
        pass