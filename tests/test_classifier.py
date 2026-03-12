import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.classifier import classify_intent

def test_classifier():
    assert classify_intent("What is return policy?") == "faq"
    assert classify_intent("Where is my order 1234?") == "order"
    assert classify_intent("I want a refund") == "refund"
    assert classify_intent("I am very angry!") == "escalate"
    print("All classifier tests passed!")

if __name__ == "__main__":
    test_classifier()