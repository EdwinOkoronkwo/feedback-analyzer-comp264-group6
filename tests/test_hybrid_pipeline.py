import os
import requests
import pytesseract
from PIL import Image
from gtts import gTTS
from dotenv import load_dotenv

# --- 1. SETUP & CONFIG ---
load_dotenv()
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
# Using your verified path
IMAGE_PATH = "/home/edwin/projects/feedback_analyzer/tests/sample_images/french.jpg"
AUDIO_OUTPUT = "output_summary.mp3"

def run_master_pipeline():
    print(f"🧬 STARTING FULL MULTIMODAL PIPELINE")
    print("="*60)

    # --- STAGE 1: LOCAL OCR (Tesseract) ---
    print("⏳ [1/3] Stage 1: Local OCR (Reading Pixels)...")
    if not os.path.exists(IMAGE_PATH):
        print(f"❌ Error: Image not found at {IMAGE_PATH}")
        return

    raw_text = pytesseract.image_to_string(Image.open(IMAGE_PATH)).strip()
    if not raw_text:
        print("❌ Error: OCR failed to extract text.")
        return
    print(f"✅ OCR Complete! Found text: \"{raw_text[:50]}...\"")

    # --- STAGE 2: CLOUD ANALYSIS (Mistral) ---
    print("\n⏳ [2/3] Stage 2: Mistral Cloud (Brain)...")
    prompt = (
        f"The following was extracted from an image: '{raw_text}'. "
        "Translate to English, summarize in one sentence, and give sentiment."
    )
    
    headers = {"Authorization": f"Bearer {MISTRAL_API_KEY}"}
    payload = {
        "model": "mistral-tiny",
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        res = requests.post("https://api.mistral.ai/v1/chat/completions", json=payload, headers=headers)
        res.raise_for_status()
        analysis = res.json()['choices'][0]['message']['content']
        print(f"✅ Analysis Complete!")
        print(f"\n--- 📊 AI INSIGHTS ---\n{analysis}\n" + "-"*30)
    except Exception as e:
        print(f"❌ Mistral Error: {e}")
        return

    # --- STAGE 3: SPEECH SYNTHESIS (gTTS) ---
    print("\n⏳ [3/3] Stage 3: Speech Generation (Voice)...")
    try:
        # We'll speak the analysis result
        tts = gTTS(text=analysis, lang='en')
        tts.save(AUDIO_OUTPUT)
        print(f"✅ Audio saved to: {AUDIO_OUTPUT}")
        
        # This will play the audio through your VM's speakers
        print("🔊 Playing Audio...")
        os.system(f"ffplay -nodisp -autoexit {AUDIO_OUTPUT} > /dev/null 2>&1")
    except Exception as e:
        print(f"❌ Speech Error: {e}")

    print("\n" + "="*60)
    print("🎊 FULL PIPELINE SUCCESSFUL!")

if __name__ == "__main__":
    run_master_pipeline()