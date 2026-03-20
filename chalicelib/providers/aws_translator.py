import boto3
from ..interfaces.translator import ITranslateProvider
from ..interfaces.logger import ILogger

class AWSTranslateProvider(ITranslateProvider):
    def __init__(self, logger: ILogger):
        self.client = boto3.client('translate')
        self.logger = logger

    def translate(self, text: str, target_lang: str = "en") -> str:
        self.logger.log_event("AWS_TRANS", "DEBUG", f"Sending: {text[:50]}")
        try:
            response = self.client.translate_text(
                Text=text, SourceLanguageCode="auto", TargetLanguageCode=target_lang
            )
            res = response.get('TranslatedText')
            self.logger.log_event("AWS_TRANS", "SUCCESS", "Translation received")
            return res
        except Exception as e:
            self.logger.log_event("AWS_TRANS_ERR", "ERROR", str(e))
            return text