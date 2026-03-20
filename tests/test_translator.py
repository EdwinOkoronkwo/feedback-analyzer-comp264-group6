from dotenv import load_dotenv

from chalicelib.utils.logger import FileAuditLogger
load_dotenv() # Crucial for your AWS Keys

from chalicelib.providers.aws_translator import AWSTranslateProvider


def test_translation_logic():
    logger = FileAuditLogger()
    translator = AWSTranslateProvider(logger=logger)
    
    # Test with a Spanish string
    test_text = "El servicio al cliente fue fantástico."
    print(f"Translating: {test_text}")
    
    result = translator.translate(test_text, target_lang="en")
    
    if "service" in result.lower():
        print(f"✅ Translation Success: {result}")
    else:
        print(f"❌ Translation Failed or returned original: {result}")

if __name__ == "__main__":
    test_translation_logic()