
# chalicelib/interfaces/sentiment.py
from abc import ABC, abstractmethod

class ISentimentProvider(ABC):
    @abstractmethod
    def analyze(self, text: str) -> dict:
        """Returns a dictionary containing sentiment (Positive/Negative) and scores"""
        pass