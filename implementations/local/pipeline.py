import os
import subprocess
import uuid
from PIL import Image
import boto3
from boto3.dynamodb.conditions import Attr
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'
from datetime import datetime
from gtts import gTTS
from implementations.local.providers.analytics import LocalAnalyticsProvider

from chalicelib.utils.converters import DataConverter

import uuid
import os
from PIL import Image
import pytesseract

class LocalPipelineOrchestrator:
    def __init__(self, persistence, ai_analyzer, sanitizer, security):
        """
        Updated constructor to accept the new modular components.
        """
        self.persistence = persistence
        self.ai = ai_analyzer
        
        # NEW: Store these so you can use them in the run() method
        self.sanitizer = sanitizer
        self.security = security

    def run(self, payload: dict):
        import logging
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger("VMware-Pipeline")
        
        logger.info("!!! PIPELINE TRIGGERED !!!")
        logger.info(f"Payload Source: {payload.get('source_type')}")
        feedback_id = payload.get("feedback_id") or str(uuid.uuid4())
        user_id = payload.get("user_id", "anonymous")
        
        print(f"\n🚀 [START] Pipeline ID: {feedback_id} for User: {user_id}")

        # --- Step 1: Text Acquisition ---
        yield 0.2, "🔍 Step 1/4: Acquiring Text..."
        raw_text = self._acquire_text(payload)
        if not raw_text:
            print(f"❌ [STEP 1 FAILED]: No text extracted for ID {feedback_id}")
            yield 0.0, "Error: No text could be acquired."
            return
        print(f"✅ [STEP 1 SUCCESS]: Extracted {len(raw_text)} characters.")

        # --- Step 2: AI Analysis ---
        yield 0.5, f"🧠 Step 2/4: AI Analysis..."
        print(f"📡 [STEP 2]: Calling Mistral API...")
        
        # LOGICAL FIX: Ensure we call 'summarize' or 'analyze' correctly
        try:
            # We use summarize() because that's what's in your MistralProvider
            ai_response = self.ai.summarize(raw_text) 
            
            if not ai_response or "Summary unavailable" in ai_response:
                print(f"❌ [STEP 2 FAILED]: Mistral returned empty or error string.")
                yield 0.0, "Error: AI Analysis failed."
                return
            print(f"✅ [STEP 2 SUCCESS]: AI Response received.")
        except Exception as e:
            print(f"🔥 [STEP 2 CRASH]: {type(e).__name__}: {str(e)}")
            yield 0.0, "Error: AI Analysis failed."
            return

        # --- Step 2.5: Audio Generation ---
        yield 0.7, "🔊 Step 2.5/4: Generating Audio..."
        audio_path = self._generate_audio(ai_response, feedback_id)
        print(f"🎵 [STEP 2.5]: Audio saved to -> {audio_path}" if audio_path else "⚠️ [STEP 2.5]: Audio failed (skipping)")

        # --- Step 3: Persistence ---
        yield 0.9, "💾 Step 3/4: Saving to Database..."
        success = self._persist_data(payload, raw_text, ai_response, user_id, feedback_id, audio_path)
        
        if not success:
            print(f"❌ [STEP 3 FAILED]: DynamoDB save failed for {feedback_id}")
            yield 0.0, "Error: Persistence failed."
            return
        print(f"✅ [STEP 3 SUCCESS]: Records saved to DynamoDB.")

        # --- Step 4: Finalization ---
        yield 0.95, "✅ Step 4/4: Finalizing Results..." # Use 0.95 so 1.0 is the "True" end
        
        # Pull the data from the aggregator
        final_data = self.persistence.get_unified_view(feedback_id)
        
        if final_data:
            print(f"🏁 [COMPLETE]: Pipeline finished successfully for {feedback_id}\n")
            
            # Ensure the UI sees the 'COMPLETE' status
            final_data["status"] = "COMPLETE" 
            
            # CRITICAL: This MUST be the final yield for the UI to stop spinning
            yield 1.0, final_data 
        else:
            print(f"❌ [STEP 4 FAILED]: Could not retrieve {feedback_id} from DB after save.")
            yield 0.0, "Error: Final retrieval failed."

    def get_final_result(self, feedback_id: str):
        """Wrapper to fetch the final unified view from the aggregator."""
        return self.persistence.get_unified_view(feedback_id)


    def _persist_data(self, payload, raw_text, ai_response, user_id, feedback_id, audio_path) -> bool:
        try:
            # 1. Create the high-level Models
            meta_obj = DataConverter.to_metadata_model(payload, raw_text, user_id, feedback_id)
            sum_obj = DataConverter.to_summary_model(feedback_id, ai_response, audio_path)

            # 2. Use your existing STATIC method to get DB-ready dicts
            # This handles Enums and Decimals perfectly!
            print(f"🔄 [Persistence]: Formatting for DynamoDB...", flush=True)
            meta_db = DataConverter.model_to_db_dict(meta_obj)
            sum_db = DataConverter.model_to_db_dict(sum_obj)

            # 3. Save directly to the Repositories
            # Ensure these Repository methods just take the DICT and save it
            self.persistence.meta_service.repo.save_metadata(meta_db)
            self.persistence.summary_service.repo.save_summary(sum_db)
            
            return True
        except Exception as e:
            print(f"❌ [Persistence Error]: {str(e)}", flush=True)
            return False

    def _acquire_text(self, payload: dict) -> str:
        if payload.get("source_type") == "IMAGE":
            try:
                return pytesseract.image_to_string(Image.open(payload["file_path"])).strip()
            except Exception: return ""
        return payload.get("text", "")

    def _acquire_text(self, payload: dict) -> str:
        # If it's a direct text submission, return it immediately
        if payload.get("source_type") != "IMAGE":
            return payload.get("text", "")

        img_path = payload.get("file_path")
        
        # Guard Clause: Path must exist
        if not img_path or not os.path.exists(img_path):
            print(f"❌ OCR Error: Image missing at {img_path}")
            return ""

        try:
            # 1. Open the image
            with Image.open(img_path) as img:
                # 2. The core OCR operation with Multi-Language Support
                # 'eng' = English, 'fra' = French, 'spa' = Spanish, 'deu' = German
                # Adding these ensures accents like é, à, ñ, and ü are recognized.
                text = pytesseract.image_to_string(img, lang='eng+fra+spa+deu').strip()
            
            if not text:
                print("⚠️ OCR Warning: No text detected in image.")
            
            return text
        except Exception as e:
            print(f"❌ OCR Critical Failure: {e}")
            return ""

    def _generate_audio(self, ai_response: str, feedback_id: str) -> str:
        """
        Generates a text-to-speech MP3 file of the AI summary.
        """
        try:
            output_dir = "storage/audio"
            os.makedirs(output_dir, exist_ok=True)
            
            file_path = f"{output_dir}/{feedback_id}.mp3"
            
            # 1. Extract the text (handling if ai_response is a dict or string)
            text_to_speak = ai_response.get('summary', str(ai_response)) if isinstance(ai_response, dict) else str(ai_response)
            
            print(f"📡 [AUDIO]: Generating TTS for {feedback_id}...", flush=True)
            
            # 2. Generate the audio using gTTS (Google TTS) or your AI provider
            from gtts import gTTS
            tts = gTTS(text=text_to_speak, lang='en')
            tts.save(file_path)
            
            return file_path
        except Exception as e:
            print(f"⚠️ [AUDIO ERROR]: {e}", flush=True)
            return "" # Return empty string so the pipeline can still finish without audio