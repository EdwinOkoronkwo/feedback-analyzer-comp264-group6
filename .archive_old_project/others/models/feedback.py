from dataclasses import dataclass, asdict, field
from datetime import datetime
import uuid

@dataclass
class FeedbackModel:
    # --- 1. Identity & Status ---
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = "anonymous"
    status: str = "PENDING"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    # --- 2. Raw Input ---
    text: str = ""           # The original text or OCR result
    image_id: str = None      # Reference to S3/Local storage
    
    # --- 3. The "Embedded" Analysis Results ---
    # Instead of separate tables, these live inside the Feedback object
    summary: str = None
    sentiment: str = None
    translated_text: str = None
    
    # --- 4. Deep-Dive Metadata (The specialized worker data) ---
    # Use dicts to store the full output from ocr_worker, label_worker, etc.
    ocr_details: dict = field(default_factory=dict)
    labels: list = field(default_factory=list)
    confidence_scores: dict = field(default_factory=dict)
    audio_metadata: dict = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        if not data: return None
        
        # 2. Aggressive mapping to satisfy the 'text' requirement
        # Check every possible place the main content might be hiding
        if 'text' not in data:
            data['text'] = data.get('summary_text') or data.get('content') or ""

        # 3. Existing mappings
        mappings = {
            'feedback_id': 'id',
            'processed_at': 'created_at',
            'username': 'user_id'
        }
        for old_key, new_key in mappings.items():
            if old_key in data and new_key not in data:
                data[new_key] = data.pop(old_key)

        # 4. Filter and return
        valid_fields = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**valid_fields)