from flask import Flask, request, jsonify
import os
import sys
import importlib.util
import pytesseract
from PIL import Image
from chalicelib.interfaces.pipeline import IPipelineBridge

class LocalPipelineBridge(IPipelineBridge):
    def __init__(self, project_root):
        self.project_root = project_root
        self.upload_folder = os.path.join(project_root, 'storage/uploads')
        os.makedirs(self.upload_folder, exist_ok=True)
        
        # Dynamically load your workers using your logic
        self.workers = self._load_all_workers()

    def _import_worker(self, worker_name):
        # Adjusted path to find the lambda folder from the new location
        path = os.path.join(self.project_root, f"lambda/{worker_name}_worker/aws_handler.py")
        spec = importlib.util.spec_from_file_location(f"{worker_name}_worker", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def _load_all_workers(self):
        try:
            workers = {
                "ocr": self._import_worker("ocr"),
                "summary": self._import_worker("summary"),
                "analysis": self._import_worker("analysis"),
                "speech": self._import_worker("speech")
            }
            print("✅ All local workers loaded successfully.")
            return workers
        except Exception as e:
            print(f"❌ Error loading workers: {e}")
            return {}

    def trigger_pipeline(self, data, file=None):
        """This is your core 'process_feedback' logic converted to a method"""
        filename = data.get('filename')
        feedback_id = data.get('feedback_id')
        initial_text = data.get('text', '')
        ocr_text = ""

        # 2. Save & Scan with Tesseract (Your logic)
        if file:
            save_path = os.path.join(self.upload_folder, filename)
            file.save(save_path)
            try:
                img = Image.open(save_path)
                ocr_text = pytesseract.image_to_string(img)
            except Exception as e:
                print(f"❌ Tesseract Failed: {e}")

        combined_text = f"{ocr_text}\n{initial_text}".strip()

        # 4. Trigger Summary Worker (Your logic)
        summary_payload = {
            "feedback_id": feedback_id,
            "text": combined_text,
            "user_id": data.get('user_id', 'admin')
        }
        
        # Call the actual handler
        final_summary = self.workers['summary'].lambda_handler({"body": summary_payload}, None)
        
        return {
            "status": "success",
            "analysis_preview": {
                "summary": final_summary.get('summary'),
                "sentiment": final_summary.get('sentiment')
            }
        }