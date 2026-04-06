import time
from flask import Flask, request, jsonify
import os
import requests
import sys
import importlib.util
import pytesseract
from PIL import Image
from chalicelib.ingestion.kag_loader import get_prepared_kag_batch
from chalicelib.interfaces.pipeline import IPipelineBridge

class LocalPipelineBridge(IPipelineBridge):
    def __init__(self, project_root):
        self.project_root = project_root
        self.upload_folder = os.path.join(project_root, 'storage/uploads')
        os.makedirs(self.upload_folder, exist_ok=True)
        
        # Load workers safely
        self.workers = self._load_all_workers()

    def _import_worker(self, worker_name):
        """Loads the worker from the handler.py file inside its folder."""
        path = os.path.join(self.project_root, f"lambda/{worker_name}_worker/handler.py")
        
        if not os.path.exists(path):
            raise FileNotFoundError(f"Worker file not found at {path}")

        spec = importlib.util.spec_from_file_location(f"{worker_name}_worker", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def _import_worker(self, worker_name):
        """Loads the worker with a cache-bust to ensure we don't get 'Ghost Generators'."""
        path = os.path.join(self.project_root, f"lambda/{worker_name}_worker/handler.py")
        
        if not os.path.exists(path):
            raise FileNotFoundError(f"Worker file not found at {path}")

        # 🎯 CACHE BUST: Remove the old version from memory if it exists
        module_name = f"{worker_name}_worker"
        if module_name in sys.modules:
            del sys.modules[module_name]

        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        return module

    def trigger_kag_ingestion(self, base_path, folder_name="Email", limit=3):
        print("🚀🚀🚀 CANARY: THE NEW BRIDGE IS RUNNING 🚀🚀🚀") # <--- Add t
        """
        🚀 FLASK DISPATCHER:
        Sends Kaggle samples to the dedicated worker API.
        """
       
        samples = get_prepared_kag_batch(base_path, folder_name=folder_name, limit=limit)
        sample_ids = []

        print(f"\n📡 [BRIDGE]: Dispatching {len(samples)} samples to Flask Worker...")

        for sample in samples:
            payload = {
                "feedback_id": sample['feedback_id'],
                "file_path": sample.get('file_path'),
                "folder": folder_name
            }

            try:
                # 🎯 THE BLOCKING CALL: Flask won't respond until the AI is finished
                resp = requests.post("http://localhost:5001/process-kag", json=payload, timeout=60)
                
                if resp.status_code == 200:
                    sample_ids.append(sample['feedback_id'])
                    print(f"✅ [DISPATCHED]: {sample['feedback_id']}")
            except Exception as e:
                print(f"❌ [FLASK-COMM-ERROR]: {e}")

        return {
            "status": "COMPLETE",
            "sample_ids": sample_ids
        }

    def trigger_pipeline(self, data, file=None):
        """Standard feedback processing logic."""
        filename = data.get('filename')
        feedback_id = data.get('feedback_id')
        initial_text = data.get('text', '')
        ocr_text = ""

        if file:
            save_path = os.path.join(self.upload_folder, filename)
            file.save(save_path)
            try:
                img = Image.open(save_path)
                ocr_text = pytesseract.image_to_string(img)
            except Exception as e:
                print(f"❌ Tesseract Failed: {e}")

        combined_text = f"{ocr_text}\n{initial_text}".strip()

        summary_payload = {
            "feedback_id": feedback_id,
            "text": combined_text,
            "user_id": data.get('user_id', 'admin')
        }
        
        if "summary" in self.workers:
            # Use body wrapping to stay consistent with Lambda Proxy integrations
            final_summary = self.workers['summary'].lambda_handler({"body": summary_payload}, None)
            return {
                "status": "success",
                "analysis_preview": {
                    "summary": final_summary.get('summary'),
                    "sentiment": final_summary.get('sentiment')
                }
            }
        return {"status": "error", "message": "Summary worker not loaded."}

    def _persist_data(self, payload, raw_text, ai_response, user_id, feedback_id, audio_path):
        table = self.persistence.summary_service.repo.table
        try:
            table.put_item(Item={
                'feedback_id': feedback_id,
                'user_id': user_id,
                'status': 'COMPLETED',  # 🎯 SET TO COMPLETED HERE
                'raw_text': raw_text,
                'summary': ai_response,
                'audio_path': audio_path,
                'timestamp': str(time.time()),
                'category': payload.get('category', 'Kaggle'),
                'master': '✅ Local Pipeline Finished'
            })
            return True
        except Exception:
            return False
    