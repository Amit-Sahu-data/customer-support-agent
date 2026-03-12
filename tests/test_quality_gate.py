import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluator import evaluate_response

def test_quality():
    result = evaluate_response(
        message="What is your return policy?",
        response="We accept returns within 30 days.",
        intent="faq",
        agent_used="FAQ Agent",
        response_time=1.0,
        run_id=None
    )
    assert result["overall"] >= 5.0
    print(f"Quality gate passed! Score: {result['overall']}/10")

if __name__ == "__main__":
    test_quality()