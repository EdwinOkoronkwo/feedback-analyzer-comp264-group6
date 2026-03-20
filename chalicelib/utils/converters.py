from decimal import Decimal
import os
from datetime import datetime
from chalicelib.models.models import MetadataModel, ProcessStatus, Sentiment, SummaryModel
from dataclasses import asdict
from enum import Enum


class DataConverter:
    @staticmethod
    def to_metadata_model(payload: dict, raw_text: str, user_id: str, feedback_id: str) -> MetadataModel:
        print(f"DEBUG [Converter]: Mapping Metadata with ID -> {feedback_id}") # LOG THIS
        
        return MetadataModel(
            feedback_id=feedback_id,
            user_id=user_id,
            source_type=payload.get("source_type", "TEXT"),
            raw_text=raw_text,
            created_at=datetime.now().isoformat()
        )

    @staticmethod
    def to_summary_model(feedback_id, ai_response, audio_path=None):
        print(f"DEBUG [Converter]: Mapping Summary with ID -> {feedback_id}") # LOG THIS
        """Logic to parse AI string into a Model, now including audio."""
        # Simple extraction logic for demonstration
        sentiment = Sentiment.NEUTRAL
        if "POSITIVE" in ai_response.upper(): sentiment = Sentiment.POSITIVE
        elif "NEGATIVE" in ai_response.upper(): sentiment = Sentiment.NEGATIVE

        return SummaryModel(
            feedback_id=feedback_id,
            summary=ai_response,
            sentiment=sentiment,
            sentiment_score=0.95, # This is a float - the next method fixes it
            status=ProcessStatus.COMPLETED,
            processed_at=datetime.now().isoformat(),
            audio_path=audio_path # <--- Pass the path here
        )

    @staticmethod
    def model_to_db_dict(model_instance) -> dict:
        """Converts Dataclass to Dict and Floats to Decimals for DynamoDB."""
        raw_data = asdict(model_instance)
        clean_data = {}
        for key, value in raw_data.items():
            if isinstance(value, Enum):
                clean_data[key] = value.value
            elif isinstance(value, float):
                # FIX: Prevents 'Float types are not supported' error
                clean_data[key] = Decimal(str(value))
            else:
                clean_data[key] = value
        return clean_data