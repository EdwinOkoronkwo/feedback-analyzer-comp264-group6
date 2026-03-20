from abc import ABC, abstractmethod

class IAnalyticsProvider(ABC):
    @abstractmethod
    def run_query(self, sql_query: str):
        """Executes a raw SQL query and returns a list of dictionaries."""
        pass

    @abstractmethod
    def get_sentiment_summary(self) -> list:
        """Returns a summary of sentiment counts across the system."""
        pass