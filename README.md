# 🛍️ ShopEasy Multi-Agent Customer Support System

A production-grade AI customer support system built with 
LangGraph, LangSmith, and LLMOps best practices.

## 🏗️ Architecture
```
User Message
     ↓
Intent Classifier (LangGraph)
     ↓
┌────┬─────┬────────┬───────────┐
FAQ  Order  Refund  Escalation
Agent Agent  Agent    Agent
     ↓
Auto Evaluation (LLM-as-Judge)
     ↓
LangSmith Observability
     ↓
SQLite Storage + Streamlit Dashboard
```

## 🤖 Agents

- **Classifier** — detects intent from every message
- **FAQ Agent** — answers policy questions using keyword search
- **Order Agent** — handles order tracking with mock DB
- **Refund Agent** — processes refunds with approval logic
- **Escalation Agent** — handles frustrated customers + human handoff

## 📊 LLMOps Features

- **LangSmith Tracing** — every agent call traced end-to-end
- **Auto Evaluation** — 4 dimensions scored per response
- **Quality Dashboard** — live metrics and trend charts
- **Human Feedback** — thumbs up/down on every response
- **Conversation History** — full audit trail with eval scores
- **CI/CD Pipeline** — GitHub Actions auto-deploys on push

## 🛠️ Tech Stack

| Tool | Purpose |
|------|---------|
| LangGraph | Multi-agent orchestration |
| LangChain | Prompts, tools, chains |
| LangSmith | Tracing + observability |
| Groq (LLaMA 3.1) | Free LLM inference |
| SQLite | Conversation storage |
| Streamlit | Chat UI + dashboard |
| Docker | Containerization |
| GitHub Actions | CI/CD pipeline |

## 🚀 Quick Start

### 1. Clone the repo
```bash
git clone https://github.com/Amit-Sahu-data/customer-support-agent.git
cd customer-support-agent
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up environment
```bash
cp .env.example .env
# Add your GROQ_API_KEY and LANGCHAIN_API_KEY
```

### 4. Initialize knowledge base
```bash
python knowledge_base/loader.py
```

### 5. Run the app
```bash
streamlit run app.py
```

## 🐳 Docker
```bash
docker build -t customer-support-agent .
docker run -p 8501:8501 --env-file .env customer-support-agent
```

## 📈 Evaluation Metrics

Every response is automatically scored on:
- **Relevance** — did agent answer what was asked?
- **Tone** — was response empathetic and professional?
- **Resolution** — did it solve the customer's problem?
- **Routing** — was the right agent used?
- **Latency** — how fast was the response?

## 🔍 LangSmith Dashboard

All traces visible at: https://smith.langchain.com
Project: `customer-support-agent`
```

---

## STEP 22 — Create .env.example

Create `.env.example`:
```
GROQ_API_KEY=your_groq_key_here
LANGCHAIN_API_KEY=your_langsmith_key_here
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=customer-support-agent
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com