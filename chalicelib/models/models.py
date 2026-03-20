from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class UserModel:
    username: str
    password_hash: str
    role: str = "user"
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            from datetime import datetime
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

    @classmethod  # <--- MUST HAVE THIS
    def from_dict(cls, data):
        if 'password' in data and 'password_hash' not in data:
            data['password_hash'] = data.pop('password')
        valid_fields = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**valid_fields)

@dataclass
class MetadataModel:
    feedback_id: str
    user_id: str
    source_type: str
    raw_text: str
    timestamp: str
    # These optional fields must be present to handle image/file data
    original_filename: Optional[str] = None
    file_path: Optional[str] = None  # <--- This was the missing link!

    @classmethod
    def from_db(cls, item: dict):
        """Strictly maps DynamoDB dictionary to the Model."""
        return cls(
            feedback_id=item.get('feedback_id'),
            user_id=item.get('user_id'),
            source_type=item.get('source_type'),
            raw_text=item.get('raw_text'),
            timestamp=item.get('timestamp'),
            original_filename=item.get('original_filename'),
            file_path=item.get('file_path')  # <--- Fixed the mapping
        )




class Sentiment(Enum):
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    NEUTRAL = "NEUTRAL"

class ProcessStatus(Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

@dataclass
class SummaryModel:
    feedback_id: str
    summary: str
    sentiment: Sentiment
    sentiment_score: float
    status: ProcessStatus
    processed_at: str
    audio_path: Optional[str] = None  # <--- Add this!

    @classmethod
    def from_db(cls, item: Dict[str, Any]):
        return cls(
            feedback_id=item['feedback_id'],
            summary=item['summary'],
            sentiment=Sentiment(item.get('sentiment', 'NEUTRAL')),
            # Use float() here; the Decimal conversion is only for SAVING to DB
            sentiment_score=float(item.get('sentiment_score', 0.0)),
            status=ProcessStatus(item.get('status', 'FAILED')),
            processed_at=item['processed_at'],
            audio_path=item.get('audio_path') # <--- Map it here
        )


@dataclass
class FeedbackModel:
    """The 'View' Model: Combined data for the UI cards."""
    feedback_id: str
    user_id: str
    title: str
    content: str
    sentiment: str
    status: str
    timestamp: str
    audio_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)