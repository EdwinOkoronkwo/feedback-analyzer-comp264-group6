from dataclasses import asdict, dataclass, field
import datetime


@dataclass
class ImageAnalysisModel:
    id: str  # Matches the parent Feedback ID
    image_url: str
    labels: list = field(default_factory=list)      # Rekognition Objects
    detected_text: str = None                       # OCR Text
    translated_ocr: str = None                      # Translated OCR
    celebrities: list = field(default_factory=list) # Rekognition Celebs
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self):
        return asdict(self)