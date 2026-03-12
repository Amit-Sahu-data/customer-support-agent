# agents/faq_agent.py
# FAQ Agent — answers general questions using ChromaDB RAG
# This agent ONLY handles general policy and how-to questions

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from knowledge_base.loader import search_faq
from dotenv import load_dotenv
import langsmith_config

load_dotenv()

llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.3)
# Why temperature=0.3 here?
# FAQ answers need slight flexibility to sound natural
# But not too high — we don't want hallucination
# 0.3 = mostly factual but naturally worded

prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful customer support agent for ShopEasy.

Answer the customer's question using ONLY the FAQ context provided.

Rules:
1. Be friendly, concise, and helpful
2. Use ONLY information from the FAQ context
3. If FAQ context does not contain the answer → say:
   "I don't have specific information about that.
    Please contact our support team at support@shopeasy.com"
4. Never make up policies or timelines not in the FAQ
5. Keep response under 100 words
6. End with "Is there anything else I can help you with?" """),
    ("human", """Customer question: {question}

FAQ Context:
{faq_context}

Please answer the customer's question.""")
])

chain = prompt | llm

def answer_faq(question: str) -> str:
    """
    Searches FAQ knowledge base and generates a helpful answer.

    Why RAG here?
    - We don't want the LLM to make up company policies
    - We retrieve the actual policy from our knowledge base
    - LLM only formats the answer — facts come from our documents
    - This is faithfulness by design — not by luck
    """
    # Step 1: Search knowledge base for relevant FAQ
    faq_context = search_faq(question, k=3)

    # Step 2: Generate answer using retrieved context
    response = chain.invoke({
        "question": question,
        "faq_context": faq_context
    })

    return response.content

if __name__ == "__main__":
    print("\n" + "="*50)
    print("Testing FAQ Agent")
    print("="*50)

    test_questions = [
        "What is your return policy?",
        "How long does delivery take?",
        "What payment methods do you accept?",
        "How do I reset my password?",
    ]

    for question in test_questions:
        print(f"\nQuestion: {question}")
        print(f"Answer: {answer_faq(question)}")
        print("-"*40)