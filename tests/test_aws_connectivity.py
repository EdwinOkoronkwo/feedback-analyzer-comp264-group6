from chalicelib.utils.logger import FileAuditLogger
from dotenv import load_dotenv
load_dotenv()

from chalicelib.providers.aws_translator import AWSTranslateProvider


def test_aws():
    logger = FileAuditLogger(name="AWS_Connectivity_Test")
    translator = AWSTranslateProvider(logger=logger)
    
    print("Testing AWS Translate connectivity...")
    try:
        res = translator.translate("Hola", target_lang="en")
        print(f"✅ AWS Response: {res}")
    except Exception as e:
        print(f"❌ AWS Connection Failed: {e}")

if __name__ == "__main__":
    test_aws()