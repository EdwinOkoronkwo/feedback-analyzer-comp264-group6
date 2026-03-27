import os
import uuid
import datetime
import boto3
import requests
import pytesseract
from PIL import Image
import pandas as pd
from gtts import gTTS
from dotenv import load_dotenv

load_dotenv()

class FeedbackSystemTest:
    def __init__(self):
        self.mistral_key = os.getenv("MISTRAL_API_KEY")
        self.db = boto3.resource(
            'dynamodb', 
            endpoint_url='http://localhost:8000',
            region_name='us-east-1',
            aws_access_key_id='local',
            aws_secret_access_key='local'
        )
        self.table_name = "Analysis_Summaries"
        self.table = self.db.Table(self.table_name)

    def extract_text_from_image(self, image_path):
        """Simulates the OCR Worker Class"""
        print(f"📷 OCR: Processing {os.path.basename(image_path)}...")
        return pytesseract.image_to_string(Image.open(image_path)).strip()

    def get_ai_analysis(self, text):
        """Simulates the Mistral Analysis Class"""
        print("🧠 AI: Requesting Mistral analysis...")
        headers = {"Authorization": f"Bearer {self.mistral_key}"}
        prompt = f"Provide: 1. Sentiment (POSITIVE/NEGATIVE/NEUTRAL) 2. English Summary. Format: SENTIMENT | SUMMARY. Text: {text}"
        
        res = requests.post(
            "https://api.mistral.ai/v1/chat/completions",
            json={"model": "mistral-tiny", "messages": [{"role": "user", "content": prompt}]},
            headers=headers
        )
        return res.json()['choices'][0]['message']['content']

    def save_to_db(self, original_text, analysis_result):
        fid = str(uuid.uuid4())
        timestamp = datetime.datetime.now().isoformat()

        # 1. THE INDEX: Write to Feedback_Master (What the UI scans first)
        master_table = self.db.Table("Feedback_Master")
        master_table.put_item(Item={
            'feedback_id': fid,
            'status': 'COMPLETED',
            'timestamp': timestamp,
            'username': 'admin' # Matches your login
        })

        # 2. THE CONTENT: Write to Analysis_Summaries
        summary_table = self.db.Table("Analysis_Summaries")
        summary_table.put_item(Item={
            'feedback_id': fid,
            'text': original_text,
            'summary': analysis_result,
            'sentiment': 'POSITIVE',
            'timestamp': timestamp
        })
        print(f"✅ Record linked in both tables. ID: {fid}")

    def run_full_flow(self, input_data, is_image=True):
        """The main controller logic"""
        print("-" * 50)
        
        # Step 1: Get raw text
        raw_text = self.extract_text_from_image(input_data) if is_image else input_data
        
        # Step 2: Get AI Analysis
        analysis = self.get_ai_analysis(raw_text)
        
        # Step 3: Persist
        sentiment = self.save_to_db(raw_text, analysis)
        
        # Step 4: Speech (Mock)
        print(f"🔊 Speech: Generated alert for {sentiment} feedback.")
        return True

# --- EXECUTION ---
if __name__ == "__main__":
    tester = FeedbackSystemTest()
    
    # TEST 1: IMAGE PATH
    image_file = "/home/edwin/projects/feedback_analyzer/tests/sample_images/french.jpg"
    if os.path.exists(image_file):
        tester.run_full_flow(image_file, is_image=True)
    
    # TEST 2: TEXT PATH
    tester.run_full_flow("The local DynamoDB connection is extremely stable on VMware!", is_image=False)

    print("\n✅ INTEGRATION TEST COMPLETE. DB IS READY FOR STREAMLIT.")