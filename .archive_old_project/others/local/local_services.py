import bcrypt
from typing import Optional, Dict, Any
from chalicelib.models.models import UserModel, MetadataModel, SummaryModel

class UserService:
    def __init__(self, repo, logger=None):
        self.repo = repo
        self.logger = logger

    def _log(self, event: str, level: str, message: str):
        if self.logger:
            self.logger.log_event(event, level, message)

    def register(self, username, password, role="user"):
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        new_user = UserModel(
            username=username,
            password_hash=hashed.decode('utf-8'),
            role=role
        )
        self.repo.save(new_user) 
        self._log("AUTH", "INFO", f"User {username} registered.")
        return new_user

    def login(self, username, password) -> Optional[UserModel]:
        user = self.repo.get_by_username(username)
        if not user:
            self._log("AUTH_LOGIN_FAIL", "WARN", f"User {username} not found.")
            return None
        if bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            self._log("AUTH_LOGIN", "INFO", f"User {username} logged in.")
            return user
        self._log("AUTH_LOGIN_FAIL", "WARN", f"Invalid password for {username}.")
        return None

    def get_user(self, username: str) -> Optional[UserModel]:
        user = self.repo.get_by_username(username)
        if not user:
            self._log("AUTH_GET_USER_FAIL", "DEBUG", f"User {username} not found.")
        return user
    
    def get_all_users(self):
        """Fetches all users from the UserRepository."""
        return self.repo.get_all_users()

class MetadataService:
    def __init__(self, repo):
        self.repo = repo

    def save_metadata(self, metadata: MetadataModel):
        return self.repo.save_metadata(metadata)

    def get_metadata(self, feedback_id: str) -> MetadataModel:
        meta = self.repo.get_metadata(feedback_id)
        if not meta:
            raise FileNotFoundError(f"Data Error: Metadata for ID {feedback_id} missing.")
        return meta

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