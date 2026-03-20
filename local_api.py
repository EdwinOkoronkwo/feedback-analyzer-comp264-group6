from flask import Flask, request, jsonify
import os
import sys
import importlib.util

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Helper to import "handler.py" from different folders without name collisions
def import_worker(worker_name):
    path = os.path.abspath(f"./lambda/{worker_name}_worker/handler.py")
    spec = importlib.util.spec_from_file_location(f"{worker_name}_worker", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Dynamically load each worker
try:
    ocr_worker = import_worker("ocr")
    label_worker = import_worker("label")
    translate_worker = import_worker("translate")
    summary_worker = import_worker("summary")
    speech_worker = import_worker("speech")
    analysis_worker = import_worker("analysis")
    print("✅ All workers loaded successfully.")
except FileNotFoundError as e:
    print(f"❌ Error loading workers: {e}")
    sys.exit(1)


import pytesseract
from PIL import Image
import os

@app.route('/process', methods=['POST'])
def process_feedback():
    UPLOAD_FOLDER = 'uploads'
    # 1. Identity & File Setup
    data = request.form.to_dict()
    filename = data.get('filename')
    feedback_id = data.get('feedback_id')
    initial_text = data.get('text', '') # Manual text from UI

    # 2. Save & Scan with Tesseract
    ocr_text = ""
    if 'file' in request.files:
        file = request.files['file']
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(save_path)
        
        # 🎯 TESSERACT INTEGRATION
        try:
            print(f"📸 [BRIDGE] Tesseract Scanning: {filename}")
            img = Image.open(save_path)
            ocr_text = pytesseract.image_to_string(img)
            print(f"📝 [BRIDGE] Tesseract found: {len(ocr_text)} characters")
        except Exception as e:
            print(f"❌ [BRIDGE] Tesseract Failed: {e}")

    # 3. Merge Text (OCR + Manual Notes)
    # This is the "Fuel" for the Summary Worker
    combined_text = f"{ocr_text}\n{initial_text}".strip()

    if not combined_text:
        return jsonify({"status": "error", "message": "No text detected in image or notes"}), 400

    # 4. Trigger Summary Worker with REAL text
    print(f"🤖 [BRIDGE] Sending text to AI Summary...")
    summary_payload = {
        "feedback_id": feedback_id,
        "text": combined_text,  # <--- NO LONGER NULL
        "user_id": data.get('user_id', 'admin')
    }
    
    final_summary = summary_worker.lambda_handler({"body": summary_payload}, None)

    return jsonify({
        "status": "success",
        "analysis_preview": {
            "summary": final_summary.get('summary'),
            "sentiment": final_summary.get('sentiment')
        }
    })


if __name__ == '__main__':
    # Initialize local filesystem
    for path in ['uploads', 'static/audio', 'static/live-data']:
        os.makedirs(path, exist_ok=True)
    
    app.run(port=5000, debug=True)