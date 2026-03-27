import bcrypt
from typing import Optional, Dict, Any

from chalicelib.models.feedback import SummaryModel



class SummaryService:
    def __init__(self, repo):
        self.repo = repo

    def save_summary(self, summary: SummaryModel):
        return self.repo.save_summary(summary)

    def get_summary(self, feedback_id: str) -> Optional[SummaryModel]:
        return self.repo.get_summary(feedback_id)      

class FeedbackAggregatorService:
    def __init__(self, meta_service, summary_service):
        self.meta_service = meta_service
        self.summary_service = summary_service

    def get_final_result(self, feedback_id):
        """Bridge method to fetch a summary by ID"""
        return self.summary_service.repo.get_summary(feedback_id)
        
    def get_by_user(self, username):
        """Bridge method for user history"""
        return self.summary_service.repo.get_by_user(username)

    def get_unified_view(self, feedback_id: str) -> Optional[Dict[str, Any]]:
        try:
            meta = self.meta_service.get_metadata(feedback_id)
            summary = self.summary_service.get_summary(feedback_id)
        except FileNotFoundError:
            return None

        if not meta:
            return None

        # This dictionary is what your test script reads
        return {
            "feedback_id": meta.feedback_id,
            "user_id": meta.user_id,
            "source_type": meta.source_type,
            "raw_text": meta.raw_text,
            "sentiment": summary.sentiment.value if summary else "NEUTRAL",
            "status": summary.status.value if summary else "PENDING",
            "content": summary.summary if summary else "Processing...",
            "processed_at": summary.processed_at if summary else None,
            "audio_path": summary.audio_path if summary else None # <--- Fixed!
        }