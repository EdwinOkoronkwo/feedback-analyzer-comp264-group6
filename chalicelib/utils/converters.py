from decimal import Decimal
from datetime import datetime
from enum import Enum
from dataclasses import asdict
from chalicelib.models import MetadataModel, SummaryModel, ProcessStatus, Sentiment

class DataConverter:
    @staticmethod
    def to_metadata_model(payload: dict, raw_text: str, user_id: str, feedback_id: str) -> MetadataModel:
        return MetadataModel(
            feedback_id=feedback_id,
            user_id=user_id,
            source_type=payload.get("source_type", "TEXT"),
            raw_text=raw_text,
            timestamp=datetime.now().isoformat(),
            original_filename=payload.get("original_filename"),
            file_path=payload.get("file_path")
        )

    @staticmethod
    def to_summary_model(feedback_id: str, ai_response: str, audio_path: str = None) -> SummaryModel:
        sentiment = Sentiment.NEUTRAL
        upper_res = ai_response.upper()
        if "POSITIVE" in upper_res: sentiment = Sentiment.POSITIVE
        elif "NEGATIVE" in upper_res: sentiment = Sentiment.NEGATIVE

        return SummaryModel(
            feedback_id=feedback_id,
            summary=ai_response,
            sentiment=sentiment,
            sentiment_score=Decimal("0.95"), # Consistency with DynamoDB
            status=ProcessStatus.COMPLETED,
            processed_at=datetime.now().isoformat(),
            audio_path=audio_path
        )

    @staticmethod
    def model_to_db_dict(model_instance) -> dict:
        """The bridge between Dataclasses and DynamoDB/UI JSON"""
        if isinstance(model_instance, dict):
            return model_instance # Already flattened
            
        raw_data = asdict(model_instance)
        clean_data = {}
        for key, value in raw_data.items():
            if isinstance(value, Enum):
                clean_data[key] = value.value
            elif isinstance(value, float):
                clean_data[key] = Decimal(str(value))
            else:
                clean_data[key] = value
        return clean_data