import re
from ..interfaces.security import ISecurity

class SimpleDataProtector(ISecurity):
    def __init__(self):
        self.email_pattern = r'[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}'
        # This updated pattern catches 7-digit (555-0199) and 10-digit (555-555-0199)
        self.phone_pattern = r'\b(\d{3}[-.]?)?\d{3}[-.]?\d{4}\b'

    def mask_sensitive_info(self, text: str) -> str:
        if not text:
            return ""
        
        text = re.sub(self.email_pattern, "[MASKED_EMAIL]", text, flags=re.IGNORECASE)
        text = re.sub(self.phone_pattern, "[MASKED_PHONE]", text)
        
        return text