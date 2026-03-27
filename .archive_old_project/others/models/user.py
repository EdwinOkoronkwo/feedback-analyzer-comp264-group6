from dataclasses import dataclass, asdict, field
from datetime import datetime
import uuid


@dataclass
class UserModel:
    username: str
    password_hash: str = None # Default to None to handle local 'password' fields
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    role: str = "user"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    @classmethod
    def from_dict(cls, data):
        # FIX: Map local 'password' to 'password_hash' if it exists
        if 'password' in data and 'password_hash' not in data:
            data['password_hash'] = data.pop('password')
            
        # FIX: Only pass arguments that the dataclass actually expects
        valid_fields = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**valid_fields)