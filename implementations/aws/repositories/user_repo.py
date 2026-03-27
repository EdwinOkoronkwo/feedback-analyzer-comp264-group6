from ...shared.base_dynamo import BaseDynamoRepository
from chalicelib.models import UserModel

class AWSUserRepository(BaseDynamoRepository):
    def __init__(self, db_resource, logger=None):
        super().__init__("Users", db_resource, logger)

    def save(self, user: UserModel):
        self.table.put_item(Item=user.to_dict())
        self._log(f"Cloud User {user.username} saved to AWS.")

    def get_by_username(self, username: str):
        item = self.get_by_id({'username': username})
        return UserModel.from_db(item) if item else None