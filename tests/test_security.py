import sys
from chalicelib.utils.security import SimpleDataProtector

def test_security_masking():
    protector = SimpleDataProtector()
    input_text = "Contact me at bob@email.com or 555-0199"
    result = protector.mask_sensitive_info(input_text)
    
    # Validation logic
    email_masked = "[MASKED_EMAIL]" in result
    phone_masked = "[MASKED_PHONE]" in result

    if email_masked and phone_masked:
        print(f"✅ Security Masking Test Passed!")
        print(f"Result: {result}")
    else:
        print(f"❌ Security Masking Failed: {result}")
        sys.exit(1) # This tells the shell script the test FAILED

if __name__ == "__main__":
    test_security_masking()