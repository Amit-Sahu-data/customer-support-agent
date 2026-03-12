# agents/refund_agent.py
# Refund Agent — handles refund and return requests
# Includes approval logic — not all refunds are auto-approved

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import langsmith_config
import re

load_dotenv()

llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.3)

# --------------------------------------------------
# Simulated refund eligibility database
# In production: query orders DB + check business rules
# --------------------------------------------------
MOCK_REFUND_ELIGIBILITY = {
    "1234": {"eligible": True,  "reason": "Within 30 day return window",
             "amount": "Rs 2,499", "item": "Wireless Headphones"},
    "5678": {"eligible": True,  "reason": "Item not yet delivered",
             "amount": "Rs 3,299", "item": "Running Shoes"},
    "9999": {"eligible": True,  "reason": "Order still processing — easy cancellation",
             "amount": "Rs 1,899", "item": "Laptop Stand"},
    "0000": {"eligible": False, "reason": "Outside 30 day return window",
             "amount": "Rs 599",  "item": "Phone Case"},
}

def check_refund_eligibility(order_id: str) -> dict:
    """
    Checks if order is eligible for refund.
    In production: complex business rules engine
    Returns dict with eligible, reason, amount, item
    """
    return MOCK_REFUND_ELIGIBILITY.get(order_id.strip(), {
        "eligible": False,
        "reason": "Order ID not found",
        "amount": "Unknown",
        "item": "Unknown"
    })

prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a refund specialist for ShopEasy.

Handle the customer's refund request professionally and empathetically.

Rules:
1. If ELIGIBLE → confirm refund initiation, give timeline (3-5 business days)
2. If NOT ELIGIBLE → explain why clearly but empathetically, offer alternatives
3. Always apologize for any inconvenience
4. Alternatives to refund: exchange, store credit, escalation to manager
5. Keep response under 120 words
6. End with "Is there anything else I can help you with?" """),
    ("human", """Customer message: {message}

Refund Eligibility:
- Order ID: {order_id}
- Eligible: {eligible}
- Reason: {reason}
- Item: {item}
- Amount: {amount}

Please handle this refund request.""")
])

chain = prompt | llm

def handle_refund_request(message: str) -> str:
    """
    Processes refund request with eligibility check.

    Why approval logic matters:
    - Not all refunds should be auto-approved
    - Business rules protect against fraud
    - Agent explains decisions clearly to customer
    - This is what real refund systems do
    """
    # Extract order ID
    order_ids = re.findall(r'\b\d{4,}\b', message)

    if order_ids:
        order_id = order_ids[0]
        eligibility = check_refund_eligibility(order_id)
    else:
        order_id = "Not provided"
        eligibility = {
            "eligible": False,
            "reason": "No order ID provided",
            "amount": "Unknown",
            "item": "Unknown"
        }

    response = chain.invoke({
        "message": message,
        "order_id": order_id,
        "eligible": eligibility["eligible"],
        "reason": eligibility["reason"],
        "item": eligibility["item"],
        "amount": eligibility["amount"]
    })

    return response.content

if __name__ == "__main__":
    print("\n" + "="*50)
    print("Testing Refund Agent")
    print("="*50)

    test_messages = [
        "I want a refund for order 1234",
        "Please cancel and refund order 5678",
        "I need to return order 0000, it's been too long",
        "I want my money back but I don't have my order number",
    ]

    for msg in test_messages:
        print(f"\nMessage: {msg}")
        print(f"Response: {handle_refund_request(msg)}")
        print("-"*40)