# agents/escalation.py
# Escalation Agent — detects frustrated customers and hands off to human
# This is the safety net of the entire system

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import langsmith_config

load_dotenv()

llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.3)

# --------------------------------------------------
# Frustration keywords — triggers escalation check
# In production: use sentiment analysis model
# For portfolio: keyword matching + LLM confirmation
# --------------------------------------------------
FRUSTRATION_KEYWORDS = [
    "angry", "furious", "terrible", "worst", "awful", "disgusting",
    "unacceptable", "ridiculous", "pathetic", "useless", "incompetent",
    "fraud", "cheating", "scam", "sue", "lawyer", "consumer court",
    "social media", "twitter", "review", "complaint", "escalate",
    "manager", "supervisor", "human", "real person", "speak to someone"
]

def detect_frustration(message: str) -> bool:
    """
    Checks if message contains frustration signals.
    Why two-layer detection?
    - Keywords catch obvious cases fast (no LLM call needed)
    - Saves API calls and reduces latency
    - LLM handles subtle frustration that keywords miss
    """
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in FRUSTRATION_KEYWORDS)

prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a senior customer support escalation specialist for ShopEasy.

The customer needs special attention — they may be frustrated or have requested human support.

Your job:
1. Acknowledge their frustration sincerely and empathetically
2. Apologize for the experience they have had
3. Inform them that a senior support agent will contact them within 2 hours
4. Collect any additional information needed
5. Make them feel heard and valued

Rules:
- Be extremely empathetic — this customer is upset
- Never be defensive about the company
- Never make promises you cannot keep
- Keep response under 150 words
- Do NOT end with a question — end with reassurance"""),
    ("human", "Customer message: {message}")
])

chain = prompt | llm

def handle_escalation(message: str) -> str:
    """
    Handles escalation to human agent.

    Why this agent matters:
    - Prevents customer churn — angry customers who feel heard often stay
    - Protects brand reputation
    - Creates audit trail in LangSmith for human review
    - In production: creates ticket in Zendesk/Freshdesk automatically
    """
    response = chain.invoke({"message": message})
    return response.content

def should_escalate(message: str) -> bool:
    """
    Determines if message should be escalated.
    Used by the graph router to decide agent routing.
    """
    return detect_frustration(message)

if __name__ == "__main__":
    print("\n" + "="*50)
    print("Testing Escalation Agent")
    print("="*50)

    test_messages = [
        "This is absolutely terrible! I want to speak to a manager NOW!",
        "I am furious! My order has been delayed for 2 weeks!",
        "Can I speak to a human agent please?",
        "I'm going to post a negative review everywhere if this isn't resolved",
        "This is a scam! I want my money back immediately!",
    ]

    for msg in test_messages:
        print(f"\nMessage: {msg}")
        print(f"Should escalate: {should_escalate(msg)}")
        print(f"Response: {handle_escalation(msg)}")
        print("-"*40)