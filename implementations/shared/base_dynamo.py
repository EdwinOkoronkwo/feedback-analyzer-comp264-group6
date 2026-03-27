from chalicelib.interfaces.repository import IRepository

class BaseDynamoRepository(IRepository):
    def __init__(self, table_name: str, db_resource, logger=None):
        self.table = db_resource.Table(table_name)
        self.logger = logger

    def _log(self, message: str, level: str = "INFO"):
        if self.logger:
            self.logger.log_event("DATABASE", level, message)

    def save(self, data_dict: dict) -> bool:
        """Generic save for DynamoDB."""
        try:
            self.table.put_item(Item=data_dict)
            return True
        except Exception as e:
            self._log(f"Save failed: {str(e)}", "ERROR")
            return False

    def get_by_id(self, key_dict: dict):
        """Generic get for DynamoDB."""
        response = self.table.get_item(Key=key_dict)
        return response.get('Item')