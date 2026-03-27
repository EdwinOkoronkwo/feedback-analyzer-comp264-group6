import requests
import os
from dotenv import load_dotenv, find_dotenv
from chalicelib.interfaces.analyzer import IAnalyzer

class MistralAnalyzer(IAnalyzer):
    def __init__(self, logger):
        """
        Mistral Provider for VMware/Local environment.
        Targets local development context and local .env keys.
        """
        load_dotenv(find_dotenv()) 
        self.api_key = os.getenv("MISTRAL_API_KEY")
        self.url = "https://api.mistral.ai/v1/chat/completions"
        self.logger = logger
        
        if not self.api_key:
            self.logger.log_event("MISTRAL_INIT", "ERROR", "Local Context: API Key missing")

    def analyze(self, text):
        """Alias to match the Orchestrator's call"""
        return self.summarize(text)

    def summarize(self, text, language="English"):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "mistral-tiny", # You can also try "mistral-small-latest"
            "messages": [
                {"role": "system", "content": f"Respond in {language}. Provide a sentiment (POSITIVE/NEGATIVE) and a brief summary."},
                {"role": "user", "content": text}
            ]
        }
        
        try:
            print(f"🌐 [Mistral API]: Connecting to {self.url}...")
            response = requests.post(self.url, json=payload, headers=headers, timeout=10)
            
            print(f"📥 [Mistral API]: Status Code: {response.status_code}")
            
            if response.status_code != 200:
                print(f"⚠️ [Mistral API]: Error Body: {response.text}")
                
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except requests.exceptions.Timeout:
            print("⏰ [Mistral API]: Connection Timed Out (Check internet/proxy)")
        except Exception as e:
            print(f"❌ [Mistral API Exception]: {str(e)}")
            return None