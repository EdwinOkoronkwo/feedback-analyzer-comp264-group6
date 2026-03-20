from dotenv import load_dotenv

from chalicelib.utils.logger import FileAuditLogger
load_dotenv()

from chalicelib.providers.sentiment_analyzer import AWSComprehendProvider


def test_sentiment_logic():
    logger = FileAuditLogger()
    analyzer = AWSComprehendProvider(logger=logger)
    
    test_text = "I am very disappointed with the delay, but the product is good."
    print(f"Analyzing: {test_text}")
    
    result = analyzer.analyze(test_text)
    
    # Check if we got a valid response structure
    if "sentiment" in result:
        print(f"✅ Sentiment Analysis Success: {result['sentiment']}")
        print(f"Scores: {result['scores']}")
    else:
        print(f"❌ Sentiment Analysis Failed: {result}")

if __name__ == "__main__":
    test_sentiment_logic()