# # chalicelib/local/local_feedback_service.py

# from typing import Optional

# from chalicelib.models.models import FeedbackModel


# class LocalFeedbackService:
#     def __init__(self, metadata_repo, summary_repo):
#         """
#         Injects the two repositories needed to assemble a full feedback view.
#         """
#         self.metadata_repo = metadata_repo
#         self.summary_repo = summary_repo

#     def get_unified_feedback(self, feedback_id: str):
#     # 1. Fetch from Metadata
#     meta = self.metadata_repo.get_metadata(feedback_id)
#     if not meta:
#         return {"error": f"Metadata missing: No record found for ID {feedback_id}"}

#     # 2. Fetch from Summary
#     summary = self.summary_repo.get_summary(feedback_id)
#     if not summary:
#         return {"error": f"Summary missing: AI processing may still be in progress for {feedback_id}"}

#     # 3. If both exist, return the full model (Success)
#     return FeedbackModel(
#         feedback_id=meta.feedback_id,
#         user_id=meta.user_id,
#         title="Manual Entry" if not meta.original_filename else meta.original_filename,
#         content=summary.summary,
#         sentiment=summary.sentiment,
#         status=summary.status,
#         timestamp=meta.timestamp
#     )