import os
import ollama
import requests
from dotenv import load_dotenv

# --- 1. CONFIGURATION ---
load_dotenv()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Adjusted path to match your sample images folder
TEST_FILE_PATH = os.path.join(BASE_DIR, "sample_images", "french.jpg")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

def run_local_pipeline():
    print(f"🚀 STARTING LOCAL PIPELINE TEST: {os.path.basename(TEST_FILE_PATH)}")
    print("="*60)

    # 1. Check for local file
    if not os.path.exists(TEST_FILE_PATH):
        print(f"❌ FILE NOT FOUND: {TEST_FILE_PATH}")
        return

    # --- STEP 2: LOCAL OCR (Ollama Vision) ---
    print("\n⏳ STAGE 1: OCR (Local Ollama Llama 3.2-Vision)...")
    try:
        ocr_response = ollama.chat(
            model='llama3.2-vision',
            messages=[{
                'role': 'user',
                'content': 'Extract all text from this image. Output ONLY the extracted text.',
                'images': [TEST_FILE_PATH]
            }]
        )
        raw_text = ocr_response['message']['content'].strip()
        print(f"✅ OCR COMPLETE: Found '{raw_text[:50]}...'")
    except Exception as e:
        print(f"❌ OCR STAGE FAILED: {e}")
        return

    # --- STEP 3: TRANSLATION & SUMMARY (Mistral Cloud) ---
    print("\n⏳ STAGE 2 & 3: Translation & Summary (Mistral Cloud)...")
    if not MISTRAL_API_KEY:
        print("❌ ERROR: MISTRAL_API_KEY not found in .env")
        return

    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # We ask Mistral to do both tasks to save on latency
    prompt = (
        f"Analyze this text extracted from an image: '{raw_text}'.\n"
        "1. Translate it into English.\n"
        "2. Provide a 1-sentence summary.\n"
        "3. Detect the sentiment (POSITIVE/NEGATIVE/NEUTRAL)."
    )

    payload = {
        "model": "mistral-tiny",
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        res = requests.post("https://api.mistral.ai/v1/chat/completions", json=payload, headers=headers)
        res.raise_for_status()
        data = res.json()['choices'][0]['message']['content']
        
        print(f"✅ ANALYSIS COMPLETE!")
        print("\n" + "-"*30)
        print(data)
        print("-"*30)
    except Exception as e:
        print(f"❌ MISTRAL STAGE FAILED: {e}")

    print("\n" + "="*60)
    print("🎊 SUCCESS: Local Pipeline Verified (No AWS used)!")

if __name__ == "__main__":
    run_local_pipeline()