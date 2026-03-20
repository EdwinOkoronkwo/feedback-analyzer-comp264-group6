import os
import subprocess
import uuid
from PIL import Image
import boto3
from boto3.dynamodb.conditions import Attr
import pytesseract
from datetime import datetime
from gtts import gTTS
from chalicelib.local.local_analytics_provider import LocalAnalyticsProvider
from chalicelib.models.models import MetadataModel, SummaryModel, Sentiment, ProcessStatus
from chalicelib.utils.converters import DataConverter

import uuid
import os
from PIL import Image
import pytesseract

class LocalPipelineOrchestrator:
    def __init__(self, persistence, ai_analyzer):
        self.persistence = persistence 
        self.ai = ai_analyzer

    def run(self, payload: dict):
        """Main entry point: Aggregates sub-steps into a generator."""
        # Fix: Ensure we use a clean UUID string throughout
        feedback_id = payload.get("feedback_id") or str(uuid.uuid4())
        user_id = payload.get("user_id", "anonymous")
        print(f"DEBUG [Orchestrator]: ID Generated -> {feedback_id}")
        
        # Step 1: Text Acquisition
        yield 0.2, "🔍 Step 1/4: Acquiring Text..."
        raw_text = self._acquire_text(payload)
        if not raw_text:
            yield 0.0, "Error: No text could be acquired."
            return

        # Step 2: AI Analysis
        yield 0.5, f"🧠 Step 2/4: AI Analysis for {user_id}..."
        ai_response = self._analyze_text(raw_text)
        if not ai_response:
            yield 0.0, "Error: AI Analysis failed."
            return

        # Step 2.5: Generate Audio from the English Summary
        yield 0.7, "🔊 Step 2.5/4: Generating Audio Narrated Summary..."
        # Audio path is generated using the UUID feedback_id
        audio_path = self._generate_audio(ai_response, feedback_id)
        print(f"DEBUG [Orchestrator]: Audio saved as -> {audio_path}") # LOG THIS

        # Step 3: Persistence
        yield 0.8, "💾 Step 3/4: Saving to Database..."
        success = self._persist_data(payload, raw_text, ai_response, user_id, feedback_id, audio_path)
        if success:
            print(f"DEBUG [Orchestrator]: Success! Fetching unified view for {feedback_id}")
            yield 1.0, self.get_final_result(feedback_id)
        else:
            yield 0.0, "Error: Persistence failed."

        # Step 4: Final Aggregation
        yield 1.0, self.get_final_result(feedback_id)

    # --- UI Bridge Methods ---
    def get_user_feedback(self, username):
        try:
            # Don't use .Table() here. Use the repo that knows how to talk to the DB.
            return self.persistence.summary_service.repo.get_by_user(username)
        except Exception as e:
            print(f"❌ Orchestrator History Error: {e}")
            return []
        
    def get_all_feedback(self):
        """Allows Admins to see every record in the system"""
        return self.persistence.summary_service.repo.get_all_feedback()

    def get_by_user(self, username):
        """Passes the request down to the persistence layer"""
        return self.persistence.summary_service.repo.get_by_user(username)

    def get_final_result(self, feedback_id):
        """
        Retrieves a single analyzed record by ID.
        Fix: Redirects to the correct repository method 'get_summary'
        """
        return self.persistence.summary_service.repo.get_summary(feedback_id)

    # Inside PipelineFactory class
    @staticmethod
    def get_local_analytics():
        # 🎯 FORCE the table name here to match what's in your worker
        return LocalAnalyticsProvider(table_name="Summaries")

    # --- Private Specialized Methods ---

    def _generate_audio(self, ai_response, feedback_id) -> str:
        """
        Generates TTS and returns the path. 
        Ensure your directory exists: ./local_db_storage/audio_outputs/
        """
        try:
            # We assume your AI provider has a tts method
            output_dir = "./local_db_storage/audio_outputs"
            os.makedirs(output_dir, exist_ok=True)
            
            file_path = f"{output_dir}/{feedback_id}.mp3"
            # Extract summary text from AI response object/dict if necessary
            text_to_speak = getattr(ai_response, 'summary', str(ai_response))
            
            self.ai.generate_tts(text_to_speak, file_path)
            return file_path
        except Exception as e:
            print(f"DEBUG: Audio Gen Failure: {e}")
            return ""

    def _persist_data(self, payload, raw_text, ai_response, user_id, feedback_id, audio_path) -> bool:
        try:
            # Use the UUID feedback_id consistently
            meta_obj = DataConverter.to_metadata_model(payload, raw_text, user_id, feedback_id)
            sum_obj = DataConverter.to_summary_model(feedback_id, ai_response, audio_path)

            # Convert to DB-ready dicts (handles Enum to String conversion)
            meta_dict = DataConverter.model_to_db_dict(meta_obj)
            sum_dict = DataConverter.model_to_db_dict(sum_obj)

            self.persistence.meta_service.repo.save_metadata(meta_dict)
            self.persistence.summary_service.repo.save_summary(sum_dict)
            return True
        except Exception as e:
            print(f"DEBUG: Persistence Failure: {e}")
            return False

    def _acquire_text(self, payload: dict) -> str:
        if payload.get("source_type") == "IMAGE":
            try:
                return pytesseract.image_to_string(Image.open(payload["file_path"])).strip()
            except Exception: return ""
        return payload.get("text", "")

    def _analyze_text(self, raw_text: str):
        try:
            return self.ai.analyze(raw_text) # Assumes your Mistral provider has an 'analyze' method
        except Exception: return None