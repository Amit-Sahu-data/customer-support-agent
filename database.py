# database.py
# Stores conversations AND evaluation scores
# Complete audit trail for every interaction

import sqlite3
from datetime import datetime

DB_PATH = "./conversations.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            message TEXT,
            intent TEXT,
            agent_used TEXT,
            response TEXT,
            response_time REAL,
            relevance_score REAL DEFAULT 0,
            tone_score REAL DEFAULT 0,
            resolution_score REAL DEFAULT 0,
            routing_score REAL DEFAULT 0,
            latency_score REAL DEFAULT 0,
            overall_score REAL DEFAULT 0,
            relevance_reason TEXT,
            tone_reason TEXT,
            resolution_reason TEXT,
            human_feedback INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()
    print("Database initialized!")

def save_conversation(message: str, intent: str,
                      agent_used: str, response: str,
                      response_time: float,
                      eval_result: dict = None):
    """
    Saves conversation with eval scores.
    eval_result is optional — saves zeros if not provided.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Extract eval scores if provided
    relevance_score = eval_result["relevance"]["score"] if eval_result else 0
    tone_score = eval_result["tone"]["score"] if eval_result else 0
    resolution_score = eval_result["resolution"]["score"] if eval_result else 0
    routing_score = eval_result["routing"]["score"] if eval_result else 0
    latency_score = eval_result["latency"]["score"] if eval_result else 0
    overall_score = eval_result["overall"] if eval_result else 0
    relevance_reason = eval_result["relevance"]["reason"] if eval_result else ""
    tone_reason = eval_result["tone"]["reason"] if eval_result else ""
    resolution_reason = eval_result["resolution"]["reason"] if eval_result else ""

    cursor.execute("""
        INSERT INTO conversations (
            timestamp, message, intent, agent_used, response,
            response_time, relevance_score, tone_score,
            resolution_score, routing_score, latency_score,
            overall_score, relevance_reason, tone_reason,
            resolution_reason
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        message, intent, agent_used, response, round(response_time, 2),
        relevance_score, tone_score, resolution_score,
        routing_score, latency_score, overall_score,
        relevance_reason, tone_reason, resolution_reason
    ))

    conn.commit()
    conn.close()

def get_all_conversations():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM conversations
        ORDER BY timestamp DESC LIMIT 100
    """)
    rows = cursor.fetchall()
    conn.close()

    columns = [
        'id', 'timestamp', 'message', 'intent', 'agent_used',
        'response', 'response_time', 'relevance_score', 'tone_score',
        'resolution_score', 'routing_score', 'latency_score',
        'overall_score', 'relevance_reason', 'tone_reason',
        'resolution_reason', 'human_feedback'
    ]
    return [dict(zip(columns, row)) for row in rows]

def get_stats():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            COUNT(*) as total,
            ROUND(AVG(response_time), 2) as avg_time,
            ROUND(AVG(overall_score), 2) as avg_quality,
            ROUND(AVG(relevance_score), 2) as avg_relevance,
            ROUND(AVG(tone_score), 2) as avg_tone,
            ROUND(AVG(resolution_score), 2) as avg_resolution,
            SUM(CASE WHEN intent='faq' THEN 1 ELSE 0 END) as faq,
            SUM(CASE WHEN intent='order' THEN 1 ELSE 0 END) as order_q,
            SUM(CASE WHEN intent='refund' THEN 1 ELSE 0 END) as refund,
            SUM(CASE WHEN intent IN ('escalate','complaint') THEN 1 ELSE 0 END) as escalation
        FROM conversations
    """)
    row = cursor.fetchone()
    conn.close()

    return {
        "total": row[0] or 0,
        "avg_response_time": row[1] or 0,
        "avg_quality": row[2] or 0,
        "avg_relevance": row[3] or 0,
        "avg_tone": row[4] or 0,
        "avg_resolution": row[5] or 0,
        "faq": row[6] or 0,
        "order": row[7] or 0,
        "refund": row[8] or 0,
        "escalation": row[9] or 0
    }

def save_feedback(conv_id: int, feedback: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE conversations SET human_feedback=? WHERE id=?",
        (feedback, conv_id)
    )
    conn.commit()
    conn.close()

if __name__ == "__main__":
    # Reset and test
    import os
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    init_db()
    save_conversation(
        message="What is your return policy?",
        intent="faq",
        agent_used="FAQ Agent",
        response="We accept returns within 30 days...",
        response_time=2.3,
        eval_result={
            "relevance": {"score": 9, "reason": "Directly answered"},
            "tone": {"score": 8, "reason": "Professional"},
            "resolution": {"score": 8, "reason": "Clear answer"},
            "routing": {"score": 10, "reason": "Correct agent"},
            "latency": {"score": 10, "reason": "Very fast"},
            "overall": 9.0
        }
    )
    stats = get_stats()
    print(f"Total: {stats['total']}")
    print(f"Avg quality: {stats['avg_quality']}/10")
    print("Database with eval scores working!")