import os
import requests
from dotenv import load_dotenv

load_dotenv()
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

def test_manual_feedback(feedback_text):
    print(f"\n✍️ TESTING DIRECT FEEDBACK: '{feedback_text}'")
    
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = (
        f"Feedback: '{feedback_text}'.\n"
        "Please provide the French translation and a sentiment analysis."
    )

    payload = {
        "model": "mistral-tiny",
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        res = requests.post("https://api.mistral.ai/v1/chat/completions", json=payload, headers=headers)
        res.raise_for_status()
        print("✅ AI Result:")
        print(res.json()['choices'][0]['message']['content'])
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_manual_feedback("The new UI update is quite confusing, but it loads faster than the old version.")