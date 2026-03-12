import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from knowledge_base.loader import search_faq

def test_search():
    result = search_faq("return policy")
    assert len(result) > 0
    print("Knowledge base test passed!")

if __name__ == "__main__":
    test_search()