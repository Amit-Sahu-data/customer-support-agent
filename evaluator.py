# evaluator.py
# Production-grade evaluation for every agent response
# Layer 1: Auto Eval using LLM-as-Judge
# Layer 2: Sends scores to LangSmith Feedback API

import os
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langsmith import Client
from dotenv import load_dotenv
import langsmith_config

load_dotenv()

llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)
langsmith_client = Client()

# --------------------------------------------------
# Score 1: Relevance
# Did the agent answer what the customer actually asked?
# --------------------------------------------------
def score_relevance(message: str, response: str) -> dict:
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a customer support quality evaluator.
Score how relevant the agent's response is to the customer's message.

Score 1-10:
10 = perfectly answers what customer asked
7  = mostly relevant, minor gaps
5  = partially relevant
3  = barely relevant
1  = completely off topic

Respond in EXACTLY this format:
SCORE: <number>
REASON: <one sentence>"""),
        ("human", f"Customer: {message}\nAgent Response: {response}")
    ])
    result = (prompt | llm).invoke({}).content.strip().split('\n')
    return {
        "score": int(result[0].replace("SCORE:", "").strip()),
        "reason": result[1].replace("REASON:", "").strip()
    }

# --------------------------------------------------
# Score 2: Tone
# Was the response empathetic and professional?
# --------------------------------------------------
def score_tone(message: str, response: str) -> dict:
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a customer support quality evaluator.
Score the tone of the agent's response.

Score 1-10:
10 = perfectly empathetic, professional, warm
7  = professional but slightly cold
5  = neutral, neither good nor bad
3  = slightly rude or dismissive
1  = rude or inappropriate

Respond in EXACTLY this format:
SCORE: <number>
REASON: <one sentence>"""),
        ("human", f"Customer: {message}\nAgent Response: {response}")
    ])
    result = (prompt | llm).invoke({}).content.strip().split('\n')
    return {
        "score": int(result[0].replace("SCORE:", "").strip()),
        "reason": result[1].replace("REASON:", "").strip()
    }

# --------------------------------------------------
# Score 3: Resolution
# Did the response actually solve the customer's problem?
# --------------------------------------------------
def score_resolution(message: str, response: str) -> dict:
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a customer support quality evaluator.
Score whether the agent's response resolves the customer's issue.

Score 1-10:
10 = completely resolves the issue with clear next steps
7  = mostly resolves but missing some details
5  = partial resolution
3  = acknowledges issue but doesn't resolve
1  = does not address the issue at all

Respond in EXACTLY this format:
SCORE: <number>
REASON: <one sentence>"""),
        ("human", f"Customer: {message}\nAgent Response: {response}")
    ])
    result = (prompt | llm).invoke({}).content.strip().split('\n')
    return {
        "score": int(result[0].replace("SCORE:", "").strip()),
        "reason": result[1].replace("REASON:", "").strip()
    }

# --------------------------------------------------
# Score 4: Routing Accuracy
# Was the right agent used for this message?
# --------------------------------------------------
def score_routing(message: str, agent_used: str, intent: str) -> dict:
    """
    Rule-based scoring — no LLM needed.
    Why rule-based here?
    - Routing is objective — right or wrong
    - Faster, cheaper, deterministic
    - LLM-as-Judge needed only for subjective qualities
    """
    correct_routing = {
        "faq": "FAQ Agent",
        "order": "Order Agent",
        "refund": "Refund Agent",
        "escalate": "Escalation Agent",
        "complaint": "Escalation Agent"
    }

    expected = correct_routing.get(intent, "FAQ Agent")
    is_correct = agent_used == expected

    return {
        "score": 10 if is_correct else 3,
        "reason": (f"Correctly routed to {agent_used}" if is_correct
                  else f"Should have used {expected}, got {agent_used}")
    }

# --------------------------------------------------
# Master eval function
# --------------------------------------------------
def evaluate_response(
    message: str,
    response: str,
    intent: str,
    agent_used: str,
    response_time: float,
    run_id: str = None
) -> dict:
    """
    Runs all 4 evaluations and sends scores to LangSmith.

    Why send to LangSmith?
    - Scores appear in LangSmith dashboard automatically
    - Can filter traces by score — find worst responses
    - Tracks quality trends over time
    - Powers A/B testing between prompt versions

    run_id: LangSmith trace ID — links eval scores to the trace
    """
    print("  Evaluating response...")

    relevance = score_relevance(message, response)
    tone = score_tone(message, response)
    resolution = score_resolution(message, response)
    routing = score_routing(message, agent_used, intent)

    # Latency score — rule based
    if response_time < 3:
        latency = {"score": 10, "reason": "Very fast under 3 seconds"}
    elif response_time < 7:
        latency = {"score": 7, "reason": "Acceptable under 7 seconds"}
    elif response_time < 15:
        latency = {"score": 5, "reason": "Slow, 7-15 seconds"}
    else:
        latency = {"score": 2, "reason": "Very slow over 15 seconds"}

    overall = round(
        (relevance["score"] + tone["score"] +
         resolution["score"] + routing["score"] +
         latency["score"]) / 5, 1
    )

    eval_result = {
        "relevance": relevance,
        "tone": tone,
        "resolution": resolution,
        "routing": routing,
        "latency": latency,
        "overall": overall
    }

    # --------------------------------------------------
    # Send scores to LangSmith Feedback API
    # Why this is powerful:
    # - Scores appear on each trace in LangSmith
    # - Can sort traces by score — find worst responses
    # - Can set alerts when score drops below threshold
    # - This is what production LLMOps teams do
    # --------------------------------------------------
    if run_id:
        try:
            for metric, data in eval_result.items():
                if metric == "overall":
                    langsmith_client.create_feedback(
                        run_id=run_id,
                        key="overall_score",
                        score=overall / 10,
                        comment=f"Overall quality: {overall}/10"
                    )
                else:
                    langsmith_client.create_feedback(
                        run_id=run_id,
                        key=metric,
                        score=data["score"] / 10,
                        comment=data["reason"]
                    )
            print("  Scores sent to LangSmith!")
        except Exception as e:
            print(f"  LangSmith feedback failed (non-critical): {e}")

    return eval_result

if __name__ == "__main__":
    print("\n" + "="*50)
    print("Testing Evaluator")
    print("="*50)

    result = evaluate_response(
        message="What is your return policy?",
        response="We accept returns within 30 days of delivery. Items must be unused and in original packaging. Electronics can be returned within 15 days only. Is there anything else I can help you with?",
        intent="faq",
        agent_used="FAQ Agent",
        response_time=2.5,
        run_id=None
    )

    print(f"\nRelevance:  {result['relevance']['score']}/10 — {result['relevance']['reason']}")
    print(f"Tone:       {result['tone']['score']}/10 — {result['tone']['reason']}")
    print(f"Resolution: {result['resolution']['score']}/10 — {result['resolution']['reason']}")
    print(f"Routing:    {result['routing']['score']}/10 — {result['routing']['reason']}")
    print(f"Latency:    {result['latency']['score']}/10 — {result['latency']['reason']}")
    print(f"\nOVERALL:    {result['overall']}/10")