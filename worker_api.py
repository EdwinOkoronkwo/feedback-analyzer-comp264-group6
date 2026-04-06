import os
import sys
import importlib.util
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- 🎯 THE "NO-FAIL" IMPORT LOGIC ---
def load_handler(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.lambda_handler

try:
    # 1. Load KAG Handler
    kag_path = "/home/edwin/projects/feedback_analyzer/lambda/kag_worker/handler.py"
    kag_handler = load_handler("kag_handler", kag_path)
    
    # 2. Load Summary Handler
    summary_path = "/home/edwin/projects/feedback_analyzer/lambda/summary_worker/handler.py"
    summary_handler = load_handler("summary_handler", summary_path)
    speech_handler = load_handler("speech", "/home/edwin/projects/feedback_analyzer/lambda/speech_worker/handler.py")
    
    print("✅ [WORKER]: Both Handlers loaded successfully via Absolute Paths.")
except Exception as e:
    print(f"❌ [WORKER]: Failed to load handlers! Error: {e}")

# --- 🚀 FLASK ROUTES ---

@app.route('/process-kag', methods=['POST'])
def handle_kag():
    event = request.get_json()
    print(f"🚀 [WORKER]: Invoking KAG Handler...")
    result = kag_handler(event, context=None)
    return jsonify(result), 200

@app.route('/process-summary', methods=['POST'])
def handle_summary():
    event = request.get_json()
    print(f"🧠 [WORKER]: Invoking Summary Handler...")
    result = summary_handler(event, context=None)
    return jsonify(result), 200

@app.route('/process-speech', methods=['POST'])
def handle_speech():
    # Pass the JSON directly to the speech lambda_handler
    return jsonify(speech_handler(request.get_json(), None)), 200

if __name__ == '__main__':
    # 🎯 threaded=True is the key to preventing the "Hanging"
    app.run(host='0.0.0.0', port=5001, threaded=True)