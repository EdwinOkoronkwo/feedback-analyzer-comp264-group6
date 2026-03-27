from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class IRepository(ABC):
    @abstractmethod
    def save(self, data: Dict[str, Any]) -> bool:
        pass

    @abstractmethod
    def get_by_id(self, entity_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def _log(self, message: str, level: str = "INFO"):
        pass