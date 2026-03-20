
from chalicelib.models.user import UserModel

class UserRepository:
    def __init__(self, db_resource, logger, table_name="Users"):
        self.table = db_resource.Table(table_name)
        self.logger = logger

    def save(self, user: UserModel):
        """Accepts a UserModel, converts to dict, and saves."""
        try:
            self.table.put_item(Item=user.to_dict())
            self.logger.log_event("USER_SAVE", "SUCCESS", f"User: {user.username}")
        except Exception as e:
            self.logger.log_event("USER_SAVE_ERR", "ERROR", str(e))

    def get_by_username(self, username: str) -> UserModel:
        """Fetches from DB and returns a UserModel instance."""
        response = self.table.get_item(Key={'username': username})
        item = response.get('Item')
        if item:
            return UserModel.from_dict(item)
        return None

    def get_all_users(self) -> list[UserModel]:
        """Fetches every user in the system for the Admin Dashboard."""
        try:
            response = self.table.scan()
            items = response.get('Items', [])
            return [UserModel.from_dict(item) for item in items]
        except Exception as e:
            self.logger.log_event("DB_SCAN_ERROR", "ERROR", str(e))
            return []