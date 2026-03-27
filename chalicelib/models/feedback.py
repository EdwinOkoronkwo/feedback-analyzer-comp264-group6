from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
from .enums import Sentiment, ProcessStatus

@dataclass
class MetadataModel:
    feedback_id: str
    user_id: str
    source_type: str
    raw_text: str
    timestamp: str
    original_filename: Optional[str] = None
    file_path: Optional[str] = None

    @classmethod
    def from_db(cls, item: dict):
        if not item: return None
        return cls(
            feedback_id=item.get('feedback_id'),
            user_id=item.get('user_id'),
            source_type=item.get('source_type'),
            raw_text=item.get('raw_text'),
            timestamp=item.get('timestamp'),
            original_filename=item.get('original_filename'),
            file_path=item.get('file_path')
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class SummaryModel:
    feedback_id: str
    summary: str
    sentiment: Sentiment
    sentiment_score: float
    status: ProcessStatus
    processed_at: str
    audio_path: Optional[str] = None

    @classmethod
    def from_db(cls, item: Dict[str, Any]):
        if not item: return None
        return cls(
            feedback_id=item['feedback_id'],
            summary=item['summary'],
            sentiment=Sentiment(item.get('sentiment', 'NEUTRAL')),
            sentiment_score=float(item.get('sentiment_score', 0.0)),
            status=ProcessStatus(item.get('status', 'FAILED')),
            processed_at=item['processed_at'],
            audio_path=item.get('audio_path')
        )

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['sentiment'] = self.sentiment.value
        data['status'] = self.status.value
        return data

@dataclass
class FeedbackModel:
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