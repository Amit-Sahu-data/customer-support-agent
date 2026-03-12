# agents/order_agent.py
# Order Agent — handles order status and tracking queries
# Simulates order database lookup (in production this hits real DB/API)

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import langsmith_config
import random

load_dotenv()

llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.3)

# --------------------------------------------------
# Simulated order database
# Why simulate? In production this would be a real DB query
# For portfolio: shows you understand the architecture
# Interviewers know this is simulated — they care about the pattern
# --------------------------------------------------
MOCK_ORDERS = {
    "1234": {"status": "Out for delivery", "eta": "Today by 8 PM",
             "item": "Wireless Headphones", "courier": "BlueDart"},
    "5678": {"status": "Shipped", "eta": "2-3 business days",
             "item": "Running Shoes", "courier": "Delhivery"},
    "9999": {"status": "Processing", "eta": "5-7 business days",
             "item": "Laptop Stand", "courier": "Not assigned yet"},
    "0000": {"status": "Delivered", "eta": "Delivered on March 10",
             "item": "Phone Case", "courier": "DTDC"},
}

def get_order_details(order_id: str) -> str:
    """
    Looks up order in mock database.
    In production: SELECT * FROM orders WHERE order_id = ?
    """
    order = MOCK_ORDERS.get(order_id.strip())
    if not order:
        return f"No order found with ID {order_id}. Please check your order ID."

    return (f"Order #{order_id}: {order['item']} | "
            f"Status: {order['status']} | "
            f"ETA: {order['eta']} | "
            f"Courier: {order['courier']}")

prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful order support agent for ShopEasy.

Help the customer with their order query using the order details provided.

Rules:
1. Be empathetic and helpful
2. If order is delayed — apologize sincerely
3. If order not found — ask customer to verify order ID
4. Provide clear next steps
5. Keep response under 100 words
6. End with "Is there anything else I can help you with?" """),
    ("human", """Customer message: {message}

Order Details: {order_details}

Please help the customer.""")
])

chain = prompt | llm

def handle_order_query(message: str) -> str:
    """
    Extracts order ID from message, looks up order, generates response.

    Why extract order ID from natural language?
    - Customers say "my order 1234" or "order #1234" or "1234"
    - We need to handle all formats
    - Simple digit extraction works for this demo
    - In production: use regex or NER for robust extraction
    """
    # Extract order ID — find any 4+ digit number in message
    import re
    order_ids = re.findall(r'\b\d{4,}\b', message)

    if order_ids:
        order_details = get_order_details(order_ids[0])
    else:
        order_details = ("No order ID found in message. "
                        "Please ask customer to provide their order ID.")

    response = chain.invoke({
        "message": message,
        "order_details": order_details
    })

    return response.content

if __name__ == "__main__":
    print("\n" + "="*50)
    print("Testing Order Agent")
    print("="*50)

    test_messages = [
        "Where is my order #1234?",
        "Can you check order 5678 for me?",
        "My order 9999 is still processing, when will it ship?",
        "I think my order was delivered but I didn't receive it, order 0000",
        "What happened to my order?",  # no order ID
    ]

    for msg in test_messages:
        print(f"\nMessage: {msg}")
        print(f"Response: {handle_order_query(msg)}")
        print("-"*40)