import boto3
from ..interfaces.sentiment import ISentimentProvider
from ..interfaces.logger import ILogger

class AWSComprehendProvider(ISentimentProvider):
    def __init__(self, logger: ILogger):
        self.client = boto3.client('comprehend')
        self.logger = logger

    def analyze(self, text: str) -> dict:
        self.logger.log_event("AWS_COMP", "DEBUG", f"Analyzing: {text[:50]}")
        try:
            response = self.client.detect_sentiment(Text=text, LanguageCode="en")
            return {"sentiment": response.get('Sentiment'), "scores": response.get('SentimentScore')}
        except Exception as e:
            self.logger.log_event("AWS_COMP_ERR", "ERROR", str(e))
            return {"sentiment": "UNKNOWN"}