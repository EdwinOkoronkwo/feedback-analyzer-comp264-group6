from chalicelib.sanitizer.feedback_sanitizer import FeedbackSanitizer
from chalicelib.utils.logger import FileAuditLogger

def test_sanitization():
    logger = FileAuditLogger()
    sanitizer = FeedbackSanitizer(logger=logger)
    
    raw_text = "   Hello &amp; Welcome!! \n\n  "
    expected = "Hello & Welcome!!"
    
    result = sanitizer.clean(raw_text)
    
    if result == expected:
        print("✅ Sanitizer Test Passed!")
    else:
        print(f"❌ Sanitizer Test Failed! Got: '{result}'")

if __name__ == "__main__":
    test_sanitization()