from abc import ABC, abstractmethod

class IDatasetProvider(ABC):
    @abstractmethod
    def create_records(self, source_path: str, destination_path: str, fraction: float = 1.0):
        """Converts raw images to TFRecord format."""
        pass

    @abstractmethod
    def get_batch(self, record_path: str, batch_size: int = 32):
        """Reads a batch of records for processing."""
        pass