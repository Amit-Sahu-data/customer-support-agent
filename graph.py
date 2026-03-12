# graph.py
# LangGraph Multi-Agent Orchestration
# This is the brain — connects all agents with conditional routing
# Every customer message flows through this graph

import sys
import os
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv
import langsmith_config

from agents.classifier import classify_intent
from agents.faq_agent import answer_faq
from agents.order_agent import handle_order_query
from agents.refund_agent import handle_refund_request
from agents.escalation import handle_escalation, should_escalate

load_dotenv()

# --------------------------------------------------
# State Definition
# Why TypedDict?
# LangGraph passes state between nodes
# Every node reads from and writes to this state
# TypedDict ensures type safety across the graph
# --------------------------------------------------
class SupportState(TypedDict):
    message: str        # original customer message
    intent: str         # classified intent
    response: str       # final agent response
    agent_used: str     # which agent handled it (for LangSmith)

# --------------------------------------------------
# Node 1: Classify Intent
# Every message enters here first
# --------------------------------------------------
def classify_node(state: SupportState) -> SupportState:
    """
    Why this is a separate node:
    - LangSmith traces this as its own step
    - Can be replaced with better classifier later
    - Clear separation of concerns
    """
    message = state["message"]

    # Check for escalation first — highest priority
    if should_escalate(message):
        intent = "escalate"
    else:
        intent = classify_intent(message)

    print(f"Intent classified: {intent}")
    return {**state, "intent": intent}

# --------------------------------------------------
# Node 2: Route to correct agent
# This is the conditional edge function
# --------------------------------------------------
def route_message(state: SupportState) -> str:
    """
    LangGraph calls this to decide which node to go to next.
    Returns the name of the next node.

    Why conditional routing matters:
    - Each agent is specialized for its domain
    - Specialized agents give much better answers
    - This is the core value of multi-agent architecture
    """
    intent = state["intent"]

    routing_map = {
        "faq": "faq_node",
        "order": "order_node",
        "refund": "refund_node",
        "complaint": "escalation_node",
        "escalate": "escalation_node",
    }

    next_node = routing_map.get(intent, "faq_node")
    print(f"Routing to: {next_node}")
    return next_node

# --------------------------------------------------
# Node 3-6: Specialized Agent Nodes
# --------------------------------------------------
def faq_node(state: SupportState) -> SupportState:
    response = answer_faq(state["message"])
    return {**state, "response": response, "agent_used": "FAQ Agent"}

def order_node(state: SupportState) -> SupportState:
    response = handle_order_query(state["message"])
    return {**state, "response": response, "agent_used": "Order Agent"}

def refund_node(state: SupportState) -> SupportState:
    response = handle_refund_request(state["message"])
    return {**state, "response": response, "agent_used": "Refund Agent"}

def escalation_node(state: SupportState) -> SupportState:
    response = handle_escalation(state["message"])
    return {**state, "response": response, "agent_used": "Escalation Agent"}

# --------------------------------------------------
# Build the Graph
# --------------------------------------------------
def build_graph():
    """
    Assembles all nodes and edges into a LangGraph.

    Graph structure:
    START → classify_node → [conditional routing] → agent_node → END

    Why LangGraph over simple if/else?
    - Visual graph structure — can be exported and visualized
    - LangSmith traces each node separately
    - Easy to add new agents — just add node + edge
    - Supports async, streaming, and checkpointing
    - Industry standard for production agent systems
    """
    graph = StateGraph(SupportState)

    # Add all nodes
    graph.add_node("classify_node", classify_node)
    graph.add_node("faq_node", faq_node)
    graph.add_node("order_node", order_node)
    graph.add_node("refund_node", refund_node)
    graph.add_node("escalation_node", escalation_node)

    # Entry point
    graph.set_entry_point("classify_node")

    # Conditional routing from classifier to agents
    graph.add_conditional_edges(
        "classify_node",
        route_message,
        {
            "faq_node": "faq_node",
            "order_node": "order_node",
            "refund_node": "refund_node",
            "escalation_node": "escalation_node",
        }
    )

    # All agent nodes end the graph
    graph.add_edge("faq_node", END)
    graph.add_edge("order_node", END)
    graph.add_edge("refund_node", END)
    graph.add_edge("escalation_node", END)

    return graph.compile()

# --------------------------------------------------
# Main compiled graph — import this everywhere
# --------------------------------------------------
support_graph = build_graph()

def process_message(message: str) -> dict:
    """
    Main entry point for the entire system.
    Takes customer message → returns response + metadata.
    """
    initial_state = {
        "message": message,
        "intent": "",
        "response": "",
        "agent_used": ""
    }

    result = support_graph.invoke(initial_state)

    return {
        "message": message,
        "intent": result["intent"],
        "response": result["response"],
        "agent_used": result["agent_used"]
    }

if __name__ == "__main__":
    print("\n" + "="*50)
    print("Testing Full Multi-Agent Graph")
    print("="*50)

    test_messages = [
        "What is your return policy?",
        "Where is my order #1234?",
        "I want a refund for order 5678",
        "This is terrible service! I am very angry!",
        "Can I speak to a human agent?",
    ]

    for msg in test_messages:
        print(f"\nMessage: {msg}")
        result = process_message(msg)
        print(f"Intent:  {result['intent']}")
        print(f"Agent:   {result['agent_used']}")
        print(f"Response: {result['response'][:150]}...")
        print("-"*40)