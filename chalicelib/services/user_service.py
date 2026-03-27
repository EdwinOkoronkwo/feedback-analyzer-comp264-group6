import bcrypt
from typing import Optional, List
from chalicelib.models import UserModel

class UserService:
    def __init__(self, repo, logger=None):
        """
        The Service layer for User-related operations.
        'repo' is an implementation of IUserRepository (AWS or Local).
        """
        self.repo = repo
        self.logger = logger

    def _log(self, event: str, level: str, message: str):
        if self.logger:
            self.logger.log_event(event, level, message)

    def register(self, username, password, role="user") -> UserModel:
        """Hashes password and persists a new user through the repository."""
        # 1. Security: Hash the password using bcrypt
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # 2. Create the Domain Model
        new_user = UserModel(
            username=username,
            password_hash=hashed.decode('utf-8'),
            role=role
        )
        
        # 3. Persist via Repository
        self.repo.save(new_user) 
        self._log("AUTH_REGISTER", "INFO", f"User {username} registered successfully.")
        return new_user

    def login(self, username, password) -> Optional[UserModel]:
        """Verifies credentials and returns a UserModel if successful."""
        user = self.repo.get_by_username(username)
        
        if not user:
            self._log("AUTH_LOGIN_FAIL", "WARN", f"Login attempt for non-existent user: {username}")
            return None
            
        # Verify the provided password against the stored hash
        if bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            self._log("AUTH_LOGIN_SUCCESS", "INFO", f"User {username} logged in.")
            return user
            
        self._log("AUTH_LOGIN_FAIL", "WARN", f"Invalid password provided for user: {username}")
        return None

    def get_user(self, username: str) -> Optional[UserModel]:
        """Retrieves a user profile by username."""
        user = self.repo.get_by_username(username)
        if not user:
            self._log("AUTH_GET_USER_FAIL", "DEBUG", f"User {username} not found in database.")
        return user
    
    def get_all_users(self) -> List[UserModel]:
        """Fetches the complete list of users from the repository."""
        return self.repo.get_all_users()

