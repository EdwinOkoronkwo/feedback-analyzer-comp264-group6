from chalicelib.repositories.base import BaseRepository
from chalicelib.models.models import UserModel, MetadataModel, SummaryModel

class AWSUserRepository(BaseRepository):
    def __init__(self, db_resource, logger=None):
        super().__init__("Users", db_resource, logger)

    def save(self, user: UserModel):
        # AWS might require specific tags or server-side encryption settings
        self.table.put_item(Item=user.to_dict())
        self._log(f"Cloud User {user.username} saved to AWS.")

    def get_by_username(self, username: str):
        response = self.table.get_item(Key={'username': username})
        return UserModel.from_db(response.get('Item')) if response.get('Item') else None