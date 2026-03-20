# chalicelib/sanitizer/logic.py

import html
from ..interfaces.sanitizer import ISanitizer
from ..interfaces.logger import ILogger

class FeedbackSanitizer(ISanitizer):
    def __init__(self, logger: ILogger):
        self.logger = logger

    def clean(self, text: str) -> str:
        # 1. Convert &amp; to &
        unescaped = html.unescape(text)
        # 2. Strip whitespace and collapse multiple spaces
        cleaned = " ".join(unescaped.strip().split())
        
        self.logger.log_event("SANITIZER", "SUCCESS", f"Cleaned: {cleaned[:30]}...")
        return cleaned