from dataclasses import dataclass, field, asdict
from datetime import datetime



@dataclass
class OCRAnalysis:
    feedback_id: str
    detected_text: str = None
    translated_text: str = None
    language: str = "en"
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

