from dataclasses import dataclass, field
import datetime


@dataclass
class MediaAnalysisModel:
    id: str                 # Matches parent FeedbackModel.id
    image_url: str          # S3 Link
    
    # OCR & Translation
    detected_text: str = None    # Text found in the image
    translated_ocr: str = None   # Text translated to user's language
    
    # Audio (Polly)
    audio_url: str = None        # S3 Link to the generated .mp3 file
    
    # Computer Vision
    labels: list = field(default_factory=list) # "Menu", "Food", "Text"
    
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())