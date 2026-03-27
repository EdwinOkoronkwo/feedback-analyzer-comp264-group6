import requests
import os
from dotenv import load_dotenv, find_dotenv
from chalicelib.interfaces.analyzer import IAnalyzer

class MistralAnalyzer(IAnalyzer):
    def __init__(self, logger):
        """
        Mistral Provider for AWS environment.
        Uses environment variables or .env file.
        """
        load_dotenv(find_dotenv()) 
        self.api_key = os.getenv("MISTRAL_API_KEY")
        self.url = "https://api.mistral.ai/v1/chat/completions"
        self.logger = logger
        
        if not self.api_key:
            self.logger.log_event("MISTRAL_INIT", "ERROR", "AWS Context: API Key missing")

    def summarize(self, text, language="English"):
        """Calls Mistral API for text summarization and sentiment."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "mistral-tiny",
            "messages": [
                {
                    "role": "system", 
                    "content": f"You are a professional analyst. Respond in {language}."
                },
                {
                    "role": "user", 
                    "content": f"Summarize and determine sentiment (POSITIVE/NEGATIVE/NEUTRAL): {text}"
                }
            ]
        }
        try:
            response = requests.post(self.url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            self.logger.log_event("MISTRAL_ERROR", "ERROR", f"AWS API Failure: {str(e)}")
            return "Summary unavailable / Résumé indisponible"