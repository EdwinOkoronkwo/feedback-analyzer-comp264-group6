from dataclasses import dataclass, field, asdict
from datetime import datetime


@dataclass
class SpeechAnalysis:
    feedback_id: str
    audio_url: str  # S3 Link to the .mp3
    voice_id: str = "Joanna"
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())