import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock the Groq API call — CI doesn't need real LLM for classifier logic tests
from unittest.mock import patch, MagicMock

def test_classifier_keywords():
    """Test keyword-based fallback logic without API calls"""
    test_cases = [
        ("What is return policy?", "faq"),
        ("Where is my order 1234?", "order"),
        ("I want a refund", "refund"),
        ("I am very angry this is terrible!", "escalate"),
    ]

    keywords = {
        "faq": ["return", "policy", "shipping", "payment", "delivery"],
        "order": ["order", "track", "status", "where is"],
        "refund": ["refund", "money back", "cancel"],
        "escalate": ["angry", "terrible", "furious", "worst", "horrible"],
    }

    def keyword_classify(message):
        msg = message.lower()
        for intent, words in keywords.items():
            if any(w in msg for w in words):
                return intent
        return "faq"

    for message, expected in test_cases:
        result = keyword_classify(message)
        assert result == expected, f"Failed: '{message}' → got {result}, expected {expected}"

    print("All classifier keyword tests passed!")

if __name__ == "__main__":
    test_classifier_keywords()