from dataclasses import dataclass, field, asdict
from datetime import datetime

@dataclass
class LabelAnalysis:
    feedback_id: str
    image_url: str
    labels: list = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

