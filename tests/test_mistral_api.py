import os

from chalicelib.providers.mistral_provider import MistralAnalyzer
from chalicelib.utils.logger import FileAuditLogger
from dotenv import load_dotenv

load_dotenv()

def test_mistral_integration():
    # 1. Check if the key is actually in the environment
    api_key = os.environ.get("MISTRAL_API_KEY")
    if not api_key:
        print("❌ ERROR: MISTRAL_API_KEY not found in environment.")
        print("💡 Run: export MISTRAL_API_KEY='your_key_here'")
        return

    logger = FileAuditLogger(name="MistralTest")
    analyzer = MistralAnalyzer(logger)

    sample_text = "The system in Edmonton is lagging during peak hours, causing delays for the engineering team."
    
    print("☁️ Contacting Mistral AI Cloud...")
    summary = analyzer.summarize(sample_text)
    
    print(f"\n📝 Result: {summary}")
    
    if summary != "Summary unavailable":
        print("\n✅ Mistral Cloud Integration Successful!")
    else:
        print("\n❌ Integration Failed. Check logs/audit.log for details.")

if __name__ == "__main__":
    test_mistral_integration()