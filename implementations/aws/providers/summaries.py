import datetime
import boto3
from boto3.dynamodb.conditions import Attr
import os

class AWSSummaryProvider:
    def __init__(self, region="us-east-1", table_name="Analysis_Summaries"):
        self.db = boto3.resource('dynamodb', region_name=region)
        self.table = self.db.Table(table_name)

    def get_all_summaries(self, category=None):
        """Fetches and normalizes data for the UI."""
        try:
            if category:
                # We filter by category, but also allow items where category is missing 
                # to catch those 9 existing records.
                response = self.table.scan(
                    FilterExpression=Attr('category').eq(category) | Attr('category').not_exists()
                )
            else:
                response = self.table.scan()

            return [self._normalize(item) for item in response.get('Items', [])]
        except Exception as e:
            print(f"❌ Error fetching summaries: {e}")
            return []


    def _normalize(self, item):
        """
        Normalizes DynamoDB data for the Streamlit UI.
        Converts Unix timestamps to readable dates and maps feedback_id.
        """
        # 1. Handle the ID (Map feedback_id to the UI's item_id)
        actual_id = item.get('feedback_id', 'Unknown')

        # 2. Handle the Date (Convert 1775104856.97 -> 2026-04-02)
        raw_ts = item.get('timestamp')
        try:
            # Convert string/float to a formatted string
            readable_date = datetime.datetime.fromtimestamp(float(raw_ts)).strftime('%Y-%m-%d %H:%M')
        except (ValueError, TypeError):
            readable_date = "N/A"

        # 3. Handle the Text/Summary
        raw_text = item.get('translated_text', "No content available.")
        # If the AI hasn't run yet, we show a snippet of the OCR text
        summary_snippet = item.get('summary', raw_text[:150] + "...")

        return {
            "item_id": actual_id,
            "category": item.get('category', 'Memo'),
            "sentiment": item.get('sentiment', 'NEUTRAL').upper(),
            "summary": summary_snippet,
            "full_text": raw_text,
            "timestamp": readable_date  # 👈 Now in "YYYY-MM-DD HH:MM" format
        }