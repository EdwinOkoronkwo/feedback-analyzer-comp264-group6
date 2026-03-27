import requests
import os

import os
from dotenv import load_dotenv, find_dotenv

class MistralAnalyzer:
    def __init__(self, logger):
        # search for .env even if we are in a subfolder
        load_dotenv(find_dotenv()) 
        
        self.api_key = os.getenv("MISTRAL_API_KEY")
        self.url = "https://api.mistral.ai/v1/chat/completions"
        self.logger = logger
        
        if not self.api_key:
            self.logger.log_event("MISTRAL_INIT", "ERROR", "API Key missing in UI context")

    def summarize(self, text, language="English"):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # We tell Mistral to be a helpful assistant that responds in the target language
        payload = {
            "model": "mistral-tiny",
            "messages": [
                {
                    "role": "system", 
                    "content": f"You are a professional analyst. Always respond in {language}."
                },
                {
                    "role": "user", 
                    "content": f"Summarize this feedback and determine if the sentiment is POSITIVE, NEGATIVE, or NEUTRAL: {text}"
                }
            ]
        }

        try:
            response = requests.post(self.url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']
        except Exception as e:
            self.logger.log_event("MISTRAL", "ERROR", str(e))
            return "Résumé indisponible" # French for "Summary unavailable"