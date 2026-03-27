import os
import sys
import uuid
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chalicelib.local.local_factory import LocalPipelineFactory
from chalicelib.models.models import MetadataModel, SummaryModel, Sentiment, ProcessStatus
from chalicelib.utils.converters import DataConverter

def seed_my_data():
    # 1. Get our services
    pipeline, user_service = LocalPipelineFactory.create_local_stack()
    persistence = pipeline.persistence

    # 2. Create your "Edwin" User
    user_service.register("analyst_edwin", "password123", role="admin")

    # 3. Define your custom data entries
    # You can add as many as you want here
    custom_entries = [
        {
            "text": "The new dashboard is incredibly intuitive!",
            "sentiment": Sentiment.POSITIVE,
            "summary": "User praised the new dashboard design for being intuitive."
        },
        {
            "text": "I hate waiting 10 seconds for the OCR to finish.",
            "sentiment": Sentiment.NEGATIVE,
            "summary": "User expressed frustration regarding OCR processing latency."
        }
    ]

    for entry in custom_entries:
        f_id = str(uuid.uuid4())
        
        # Build Metadata Model
        meta = MetadataModel(
            feedback_id=f_id,
            user_id="analyst_edwin",
            source_type="TEXT",
            raw_text=entry["text"],
            timestamp=datetime.now().isoformat()
        )

        # Build Summary Model (matching our persistence requirements)
        summary = SummaryModel(
            feedback_id=f_id,
            summary=entry["summary"],
            sentiment=entry["sentiment"],
            sentiment_score=0.99 if entry["sentiment"] == Sentiment.POSITIVE else 0.1,
            status=ProcessStatus.COMPLETED,
            processed_at=datetime.now().isoformat(),
            audio_path=f"./local_db_storage/audio_outputs/{f_id}.mp3"
        )

        # Convert and Save
        persistence.meta_service.repo.save_metadata(DataConverter.model_to_db_dict(meta))
        persistence.summary_service.repo.save_summary(DataConverter.model_to_db_dict(summary))
        
        print(f"✅ Manually Seeded: {entry['summary'][:30]}...")

if __name__ == "__main__":
    seed_my_data()