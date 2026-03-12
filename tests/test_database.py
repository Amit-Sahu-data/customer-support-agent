import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import init_db, save_conversation, get_stats

def test_database():
    init_db()
    save_conversation("test", "faq", "FAQ Agent", "test response", 1.0)
    stats = get_stats()
    assert stats["total"] >= 1
    print("Database test passed!")

if __name__ == "__main__":
    test_database()