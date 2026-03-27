from dataclasses import dataclass, asdict
from typing import Dict, Any
from datetime import datetime

@dataclass
class UserModel:
    username: str
    password_hash: str
    role: str = "user"
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    @classmethod
    def from_db(cls, item: Dict[str, Any]):
        if not item: return None
        return cls(
            username=item['username'],
            password_hash=item['password_hash'],
            role=item.get('role', 'user'),
            created_at=item.get('created_at', '')
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)