import boto3
import pandas as pd
from chalicelib.utils.logger import FileAuditLogger

import boto3
import pandas as pd
from chalicelib.utils.logger import FileAuditLogger

import boto3
import pandas as pd
from chalicelib.utils.logger import FileAuditLogger

class ResultsChecker:
    def __init__(self, region="us-east-1"):
        self.logger = FileAuditLogger(name="ResultsChecker")
        self.db = boto3.resource('dynamodb', region_name=region)
        self.s3 = boto3.client('s3', region_name=region)

    def get_summary_by_id(self, feedback_id):
        """
        The 'Old Name' bridge. 
        Looks specifically in the Summaries table for the UI.
        """
        return self.get_result_from_table("Analysis_Summaries", feedback_id)

    def get_result_from_table(self, table_name, feedback_id):
        try:
            table = self.db.Table(table_name)
            
            if table_name == "Analysis_Translations":
                # Instead of get_item (which requires the exact Sort Key), 
                # we use query() to find ANY language entry for this file.
                from boto3.dynamodb.conditions import Key
                response = table.query(
                    KeyConditionExpression=Key('feedback_id').eq(feedback_id)
                )
                items = response.get('Items', [])
                # Return the first one found (or 'en' if available)
                for item in items:
                    if item.get('language') == 'en':
                        return item
                return items[0] if items else None
            
            else:
                # Standard lookup for OCR, Labels, Summaries
                response = table.get_item(Key={'feedback_id': feedback_id})
                return response.get('Item')
                
        except Exception as e:
            print(f"Error fetching from {table_name}: {e}")
            return None

    def debug_pipeline(self, feedback_id):
        """Enhanced Diagnostic with actual data previews."""
        tables = ["Analysis_Labels", "Analysis_OCR", "Analysis_Translations", "Analysis_Summaries"]
        print(f"\n🔍 DIAGNOSING PIPELINE FOR: {feedback_id}")
        print("-" * 50)
        
        for t in tables:
            item = self.get_result_from_table(t, feedback_id)
            if item:
                # We found it! Let's see what key it actually used
                actual_key = item.get('feedback_id')
                print(f"{t:25} : ✅ FOUND (Key: {actual_key})")
                
                # Check for nested content to explain why UI might be 'N/A'
                if t == "Analysis_Translations" and not item.get('translated_text'):
                    print("   ⚠️  WARNING: Row exists but 'translated_text' field is EMPTY.")
            else:
                print(f"{t:25} : ❌ MISSING")

    def display_table(self, table_name):
        """CLI method for Orchestrator verification."""
        self.logger.log_event("DB_SCAN", "INFO", f"🔎 Checking table '{table_name}'...")
        table = self.db.Table(table_name)
        try:
            response = table.scan()
            items = response.get('Items', [])
            if not items:
                return
            df = pd.DataFrame(items)
            if 'feedback_id' in df.columns:
                cols = ['feedback_id'] + [c for c in df.columns if c != 'feedback_id']
                df = df[cols]
            print(f"\n📊 Results for {table_name}:")
            print(df.to_string(index=False))
        except Exception as e:
            self.logger.log_event("SCAN_ERROR", "ERROR", str(e))

    def display_speech_results(self, bucket_name):
        """CLI method for S3 audio link verification."""
        try:
            response = self.s3.list_objects_v2(Bucket=bucket_name, Prefix='audio/')
            if 'Contents' in response:
                for obj in response['Contents']:
                    url = f"https://{bucket_name}.s3.amazonaws.com/{obj['Key']}"
                    print(f"🔊 {obj['Key'].split('/')[-1]}: {url}")
        except Exception as e:
            print(f"❌ Error: {str(e)}")

    def debug_pipeline(self, feedback_id):
        """Enhanced Diagnostic with actual data previews."""
        tables = ["Analysis_Labels", "Analysis_OCR", "Analysis_Translations", "Analysis_Summaries"]
        print(f"\n🔍 DIAGNOSING PIPELINE FOR: {feedback_id}")
        print("-" * 50)
        
        for t in tables:
            item = self.get_result_from_table(t, feedback_id)
            if item:
                # We found it! Let's see what key it actually used
                actual_key = item.get('feedback_id')
                print(f"{t:25} : ✅ FOUND (Key: {actual_key})")
                
                # Check for nested content to explain why UI might be 'N/A'
                if t == "Analysis_Translations" and not item.get('translated_text'):
                    print("   ⚠️  WARNING: Row exists but 'translated_text' field is EMPTY.")
            else:
                print(f"{t:25} : ❌ MISSING")

    def get_translations_for_id(self, feedback_id):
        """
        Fetches all translations and the AI summary for a specific file.
        """
        # 1. Fetch Translations (from Analysis_Translations table)
        trans_table = self.db.Table('Analysis_Translations')
        trans_response = trans_table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('feedback_id').eq(feedback_id)
        )
        translations = trans_response.get('Items', [])

        # 2. Fetch Summary (from Analysis_Summaries table)
        summary_table = self.db.Table('Analysis_Summaries')
        sum_response = summary_table.get_item(
            Key={'feedback_id': feedback_id}
        )
        summary = sum_response.get('Item', {})

        # Return them in a structured dictionary the pipeline expects
        return {
            "translations": translations,
            "summary": summary
        }