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

    def _load_all_workers(self):
        """Standardized worker list including the new kag_worker."""
        worker_list = ["ocr", "summary", "analysis", "speech", "mnist_ingestor", "kag"]
        loaded_workers = {}
        
        for w in worker_list:
            try:
                loaded_workers[w] = self._import_worker(w)
                print(f"✅ Loaded {w} worker.")
            except Exception as e:
                print(f"⚠️ Skipping {w} worker due to error: {e}")
        
        return loaded_workers

    def trigger_kag_ingestion(self, base_path, folder_name="Email", limit=5):
        """
        Local entry point for Kaggle Tobacco Ingestion.
        Mimics the cloud bridge but calls the local kag_worker/handler.py.
        """
        print(f"🌉 Bridge: Routing to Local KAG Worker ({folder_name})...")
        
        worker = self.workers.get("kag")
        if not worker:
            return {"status": "error", "message": "KAG worker is not available locally."}

        try:
            # Mock the Lambda event for the local kag_worker
            payload = {
                "base_path": base_path,
                "folder": folder_name,
                "limit": limit,
                "is_local": True
            }
            # Execute the handler logic locally
            return worker.lambda_handler(payload, None)
        except Exception as e:
            print(f"❌ Local KAG Ingestion Failed: {e}")
            return {"status": "error", "message": str(e)}

    def trigger_dataset_ingestion(self, payload):
        """Direct entry point for MNIST baseline test."""
        print(f"🌉 Bridge: Routing to MNIST Ingestor...")
        worker = self.workers.get("mnist_ingestor")
        
        if not worker:
            return {"status": "error", "message": "MNIST worker is not available."}

        try:
            return worker.lambda_handler(payload, None)
        except Exception as e:
            return {"status": "error", "message": str(e)}

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
    