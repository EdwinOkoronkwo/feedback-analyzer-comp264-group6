import bcrypt

from chalicelib.models.models import UserModel

class UserManager:
    def __init__(self, storage, logger):
        self.storage = storage  # This is your UserRepository instance
        self.logger = logger

    def register(self, username, password, role="user"):
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Matches the lean UserModel
        new_user = UserModel(
            username=username,
            password_hash=hashed.decode('utf-8'),
            role=role
        )
        
        self.storage.save(new_user) 
        self.logger.log_event("AUTH", "INFO", f"User {username} registered.")
        return new_user

    def login(self, username, password):
        """Verifies credentials and returns a UserModel if successful."""
        # 4. Retrieval: Call the repository's .get_by_username() method
        user = self.storage.get_by_username(username)
        
        if not user:
            self.logger.log_event("AUTH_LOGIN_FAIL", "WARN", f"User {username} not found.")
            return None
            
        # 5. Security: Verify hash (Requirement 4a)
        if bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            self.logger.log_event("AUTH_LOGIN", "INFO", f"User {username} logged in.")
            return user
            
        self.logger.log_event("AUTH_LOGIN_FAIL", "WARN", f"Invalid password for {username}.")
        return None

    def get_user(self, username):
        """Retrieves a user by username for verification or profile needs."""
        return self.storage.get_by_username(username)