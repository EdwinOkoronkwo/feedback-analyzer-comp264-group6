# chalicelib/interfaces/logger.py

from abc import ABC, abstractmethod

class ILogger(ABC):
    @abstractmethod
    def log_event(self, event_type: str, status: str, message: str):
        """Records an audit log entry"""
        pass