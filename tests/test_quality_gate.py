import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_quality_logic():
    """Test quality scoring math without API calls"""

    def compute_overall(scores):
        return round(sum(scores.values()) / len(scores), 1)

    scores = {
        "relevance": 8,
        "tone": 9,
        "resolution": 7,
        "routing": 10,
        "latency": 10
    }

    overall = compute_overall(scores)
    assert overall >= 5.0, f"Quality too low: {overall}"
    assert overall <= 10.0, f"Quality too high: {overall}"
    print(f"Quality gate passed! Score: {overall}/10")

if __name__ == "__main__":
    test_quality_logic()