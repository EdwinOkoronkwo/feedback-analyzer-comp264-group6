import sys
import os
import boto3
from boto3.dynamodb.conditions import Key

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_backend_to_ui_mapping():
    print("🧪 STARTING FINAL DATA LOGIC VERIFICATION\n" + "="*40)
    
    test_id = "spanish.jpg" 
    db = boto3.resource('dynamodb', region_name="us-east-1")
    
    # 1. OCR Check
    print(f"🔍 Testing OCR Fetch for: {test_id}")
    ocr_table = db.Table("Analysis_OCR")
    ocr_data = ocr_table.get_item(Key={'feedback_id': test_id}).get('Item', {})
    
    if ocr_data:
        lines = ocr_data.get('text_content', [])
        print(f"✅ FOUND OCR: {len(lines)} lines detected.")
        print(f"📝 SOURCE PREVIEW: {' '.join(lines)[:50]}...")
    else:
        print("❌ FAILED: OCR data missing.")

    # 2. Translation Check (The "Multi-Language" Fix)
    print(f"\n🔍 Testing Translation Fetch for: {test_id}")
    trans_table = db.Table("Analysis_Translations")
    # Query all available translations
    response = trans_table.query(KeyConditionExpression=Key('feedback_id').eq(test_id))
    items = response.get('Items', [])
    
    if items:
        # LOGIC: Specifically look for the English target
        english_item = next((i for i in items if i.get('language') == 'en'), None)
        
        if english_item:
            print(f"✅ FOUND TARGET: Language: [en]")
            print(f"🌍 TARGET PREVIEW: {english_item.get('translated_text')[:50]}...")
        else:
            found_langs = [i.get('language') for i in items]
            print(f"⚠️  PARTIAL: Found {found_langs}, but 'en' is missing. Summary will not trigger.")
    else:
        print("❌ FAILED: No translations found.")

    # 3. Summary Check
    print(f"\n🔍 Testing Summary Fetch for: {test_id}")
    sum_table = db.Table("Analysis_Summaries")
    sum_data = sum_table.get_item(Key={'feedback_id': test_id}).get('Item', {})
    
    if sum_data:
        # Note: Checking for the updated key 'summary_text' we set in the Lambda
        text = sum_data.get('summary_text') or sum_data.get('summary_output')
        print(f"✅ FOUND SUMMARY: {text[:50]}...")
    else:
        print("❌ FAILED: Summary not found. (Wait for 'en' translation to finish first)")

if __name__ == "__main__":
    test_backend_to_ui_mapping()