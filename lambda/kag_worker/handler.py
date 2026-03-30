import os
import time
import pytesseract
from PIL import Image

def lambda_handler(event, context=None):
    """
    Local KAG Worker: Process Kaggle Tobacco documents entirely on the local machine.
    Triggered by: LocalPipelineBridge
    """
    base_path = event.get('base_path')
    folder = event.get('folder', 'Email')
    limit = event.get('limit', 5)
    
    target_dir = os.path.join(base_path, folder)
    results = []

    print(f"🏠 [LOCAL KAG WORKER] Scanning: {target_dir}")

    if not os.path.exists(target_dir):
        return {"status": "error", "message": f"Path not found: {target_dir}"}

    # 1. Get local files
    files = [f for f in os.listdir(target_dir) if f.endswith(('.jpg', '.jpeg'))][:limit]

    for filename in files:
        file_path = os.path.join(target_dir, filename)
        fid = f"local_kag_{int(time.time())}_{filename}"

        try:
            # 2. Local OCR (Replacing Textract)
            print(f"🔍 [OCR] Processing {filename}...")
            raw_text = pytesseract.image_to_string(Image.open(file_path))

            # 3. Simulate Analysis (Local Logic)
            summary = f"Local Analysis of {filename}: Detected {len(raw_text)} characters."
            
            results.append({
                "feedback_id": fid,
                "status": "COMPLETED",
                "raw_text": raw_text[:200] + "...", # Preview
                "summary": summary
            })
        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")

    return {
        "status": "success",
        "processed_count": len(results),
        "results": results
    }