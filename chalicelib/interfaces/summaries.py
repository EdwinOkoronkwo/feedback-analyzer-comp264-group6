from abc import ABC, abstractmethod

class ISummariesProvider(ABC):
    @abstractmethod
    def get_all_summaries(self, category: str):
        pass

    @abstractmethod
    def get_summary_by_id(self, item_id: str):
        pass