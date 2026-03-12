# agents/classifier.py
# Intent Classifier Agent
# Reads customer message and classifies into one of 5 intents
# This is the ROUTER — every message passes through here first

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import langsmith_config  # activates LangSmith tracing automatically # activates LangSmith tracing automatically

load_dotenv()

# Why temperature=0?
# Classification needs to be deterministic — same input should
# always give same intent. Temperature=0 removes randomness.
llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)

# Why these 5 intents?
# They cover 95% of all e-commerce support queries
# Each intent maps to a specialized agent
INTENTS = ["faq", "order", "refund", "complaint", "escalate"]

prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a customer support intent classifier for ShopEasy.

Classify the customer message into EXACTLY one of these intents:
- faq        : general questions about policies, how things work, payment methods
- order      : questions about specific order status, tracking, delivery
- refund     : requests for refund, return, or money back  
- complaint  : customer is angry, frustrated, or reporting a problem
- escalate   : customer explicitly asks for human agent or manager

Rules:
1. Respond with ONLY the intent word — nothing else
2. If angry tone detected → escalate
3. If asking about a specific order → order
4. If asking how to do something → faq
5. If requesting money back → refund

Examples:
"Where is my order #1234?" → order
"What is your return policy?" → faq
"I want a refund for order 5678" → refund
"This is ridiculous, I am very angry!" → escalate
"I received a damaged product" → complaint"""),
    ("human", "{message}")
])

chain = prompt | llm

def classify_intent(message: str) -> str:
    """
    Classifies customer message into one of 5 intents.
    Returns intent string: faq/order/refund/complaint/escalate

    Why this matters:
    - Routes message to the right specialized agent
    - Specialized agents give much better answers than one general agent
    - This is the same pattern used by companies like Intercom and Zendesk
    """
    response = chain.invoke({"message": message})
    intent = response.content.strip().lower()

    # Validate — if LLM returns unexpected value, default to faq
    if intent not in INTENTS:
        print(f"Unexpected intent: {intent} — defaulting to faq")
        intent = "faq"

    return intent

if __name__ == "__main__":
    print("\n" + "="*50)
    print("Testing Intent Classifier")
    print("="*50)

    test_messages = [
        "Where is my order #12345?",
        "What is your return policy?",
        "I want a refund for my damaged product",
        "This is absolutely terrible service! I am furious!",
        "Can I speak to a human please?",
        "How do I apply a coupon code?",
        "My payment failed but money was deducted",
    ]

    for msg in test_messages:
        intent = classify_intent(msg)
        print(f"Message: {msg}")
        print(f"Intent:  {intent}")
        print("-"*40)