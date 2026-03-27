from abc import ABC, abstractmethod

class IAnalyzer(ABC):
    @abstractmethod
    def summarize(self, text: str, language: str = "English") -> str:
        pass