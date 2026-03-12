# app.py
# Production-grade Streamlit UI with evaluation built in
# Chat + Eval scores + Dashboard + History
# Pre-load embedding model before Streamlit processes anything
# This prevents timeout during first user message
import os
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
from dotenv import load_dotenv
import langsmith_config
from graph import process_message
from evaluator import evaluate_response
from database import (init_db, save_conversation, get_all_conversations,
                      get_stats, save_feedback)

load_dotenv()

st.set_page_config(
    page_title="ShopEasy Support",
    page_icon="🛍️",
    layout="wide"
)

init_db()

st.title("🛍️ ShopEasy AI Customer Support")
st.caption("Multi-Agent System | LangGraph + LangSmith | Auto-Evaluated")

tab1, tab2, tab3 = st.tabs(["💬 Chat", "📊 Dashboard", "📋 History"])

# ══════════════════════════════════════════
# TAB 1: CHAT
# ══════════════════════════════════════════
with tab1:
    st.subheader("How can we help you today?")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if msg["role"] == "assistant" and "meta" in msg:
                meta = msg["meta"]
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.caption(f"🤖 {meta['agent_used']}")
                with col2:
                    st.caption(f"🎯 Intent: {meta['intent']}")
                with col3:
                    st.caption(f"⏱️ {meta['response_time']}s")
                with col4:
                    if meta.get("overall_score"):
                        score = meta["overall_score"]
                        color = "🟢" if score >= 8 else "🟡" if score >= 6 else "🔴"
                        st.caption(f"{color} Quality: {score}/10")

    # Chat input
    # Handle quick button input
    if "quick_input" in st.session_state and st.session_state.quick_input:
        user_input = st.session_state.quick_input
        st.session_state.quick_input = None
    else:
        user_input = st.chat_input("Type your message here...")

    if user_input:
        st.session_state.messages.append({
            "role": "user", "content": user_input
        })
        with st.chat_message("user"):
            st.write(user_input)

        with st.chat_message("assistant"):
            # Step 1: Process through agent graph
            with st.spinner("Finding best agent..."):
                start_time = time.time()
                result = process_message(user_input)
                response_time = round(time.time() - start_time, 2)

            st.write(result["response"])

            # Step 2: Evaluate response
            with st.spinner("Evaluating quality..."):
                eval_result = evaluate_response(
                    message=user_input,
                    response=result["response"],
                    intent=result["intent"],
                    agent_used=result["agent_used"],
                    response_time=response_time,
                    run_id=None
                )

            # Show metadata
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.caption(f"🤖 {result['agent_used']}")
            with col2:
                st.caption(f"🎯 Intent: {result['intent']}")
            with col3:
                st.caption(f"⏱️ {response_time}s")
            with col4:
                score = eval_result["overall"]
                color = "🟢" if score >= 8 else "🟡" if score >= 6 else "🔴"
                st.caption(f"{color} Quality: {score}/10")

            # Show eval breakdown
            with st.expander("📊 See quality evaluation"):
                c1, c2, c3, c4, c5 = st.columns(5)
                with c1:
                    st.metric("Relevance",
                             f"{eval_result['relevance']['score']}/10")
                with c2:
                    st.metric("Tone",
                             f"{eval_result['tone']['score']}/10")
                with c3:
                    st.metric("Resolution",
                             f"{eval_result['resolution']['score']}/10")
                with c4:
                    st.metric("Routing",
                             f"{eval_result['routing']['score']}/10")
                with c5:
                    st.metric("Latency",
                             f"{eval_result['latency']['score']}/10")

                st.divider()
                st.write(f"**Relevance:** {eval_result['relevance']['reason']}")
                st.write(f"**Tone:** {eval_result['tone']['reason']}")
                st.write(f"**Resolution:** {eval_result['resolution']['reason']}")

            # Human feedback buttons
            st.write("Was this helpful?")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("👍 Yes", key=f"up_{len(st.session_state.messages)}"):
                    st.success("Thank you for your feedback!")
            with col2:
                if st.button("👎 No", key=f"down_{len(st.session_state.messages)}"):
                    st.warning("Sorry! We'll work on improving this.")

        # Save to database
        save_conversation(
            message=user_input,
            intent=result["intent"],
            agent_used=result["agent_used"],
            response=result["response"],
            response_time=response_time,
            eval_result=eval_result
        )

        st.session_state.messages.append({
            "role": "assistant",
            "content": result["response"],
            "meta": {
                "agent_used": result["agent_used"],
                "intent": result["intent"],
                "response_time": response_time,
                "overall_score": eval_result["overall"]
            }
        })

    # Quick question buttons
    # Quick question buttons
    st.divider()
    st.caption("Try these:")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("📦 Track Order #1234"):
            st.session_state.quick_input = "Where is my order #1234?"
            st.rerun()
    with col2:
        if st.button("↩️ Return Policy"):
            st.session_state.quick_input = "What is your return policy?"
            st.rerun()
    with col3:
        if st.button("💰 Refund Order 5678"):
            st.session_state.quick_input = "I want a refund for order 5678"
            st.rerun()
    with col4:
        if st.button("😠 Angry Customer"):
            st.session_state.quick_input = "This is terrible! I am very angry!"
            st.rerun()

# ══════════════════════════════════════════
# TAB 2: DASHBOARD
# ══════════════════════════════════════════
with tab2:
    st.subheader("📊 Live Operations Dashboard")
    st.caption("Real-time metrics — auto-refreshes when you switch tabs")

    stats = get_stats()

    if stats["total"] == 0:
        st.info("No conversations yet. Start chatting to see metrics!")
    else:
        # Row 1 — Volume metrics
        st.markdown("### Volume")
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Total Conversations", stats["total"])
        with col2:
            st.metric("FAQ Queries", stats["faq"])
        with col3:
            st.metric("Order Queries", stats["order"])
        with col4:
            st.metric("Refund Requests", stats["refund"])
        with col5:
            st.metric("Escalations", stats["escalation"])

        st.divider()

        # Row 2 — Quality metrics
        st.markdown("### Quality Scores")
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            score = stats["avg_quality"]
            delta_color = "normal" if score >= 8 else "inverse"
            st.metric("Overall Quality", f"{score}/10")
        with col2:
            st.metric("Avg Relevance", f"{stats['avg_relevance']}/10")
        with col3:
            st.metric("Avg Tone", f"{stats['avg_tone']}/10")
        with col4:
            st.metric("Avg Resolution", f"{stats['avg_resolution']}/10")
        with col5:
            st.metric("Avg Response Time", f"{stats['avg_response_time']}s")

        st.divider()

        # Charts
        convs = get_all_conversations()
        df = pd.DataFrame(convs)

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Intent Distribution")
            intent_data = pd.DataFrame({
                "Intent": ["FAQ", "Order", "Refund", "Escalation"],
                "Count": [stats["faq"], stats["order"],
                         stats["refund"], stats["escalation"]]
            })
            intent_data = intent_data[intent_data["Count"] > 0]
            if not intent_data.empty:
                fig1 = px.pie(
                    intent_data, values="Count", names="Intent",
                    color_discrete_sequence=[
                        "#4CAF50", "#2196F3", "#FF9800", "#F44336"
                    ]
                )
                st.plotly_chart(fig1, use_container_width=True)

        with col2:
            st.subheader("Quality Scores by Dimension")
            quality_data = pd.DataFrame({
                "Dimension": ["Relevance", "Tone", "Resolution"],
                "Score": [stats["avg_relevance"], stats["avg_tone"],
                         stats["avg_resolution"]]
            })
            fig2 = px.bar(
                quality_data, x="Dimension", y="Score",
                color="Dimension",
                color_discrete_sequence=["#4CAF50", "#2196F3", "#FF9800"],
                range_y=[0, 10]
            )
            st.plotly_chart(fig2, use_container_width=True)

        # Overall quality trend
        if len(df) > 1:
            st.subheader("Quality Score Trend")
            fig3 = px.line(
                df, x="timestamp", y="overall_score",
                color="agent_used",
                markers=True,
                title="Quality Over Time per Agent",
                range_y=[0, 10]
            )
            fig3.add_hline(
                y=8, line_dash="dash",
                line_color="green",
                annotation_text="Quality Gate (8.0)"
            )
            st.plotly_chart(fig3, use_container_width=True)

        # LangSmith link
        st.divider()
        st.info(
            "🔍 Deep traces, token costs, prompt versions → "
            "[Open LangSmith Dashboard](https://smith.langchain.com)"
        )

# ══════════════════════════════════════════
# TAB 3: HISTORY
# ══════════════════════════════════════════
with tab3:
    st.subheader("📋 Conversation History with Eval Scores")

    convs = get_all_conversations()

    if not convs:
        st.info("No conversations yet!")
    else:
        # Filters
        col1, col2 = st.columns(2)
        with col1:
            intent_filter = st.selectbox(
                "Filter by intent:",
                ["All", "faq", "order", "refund", "escalate", "complaint"]
            )
        with col2:
            quality_filter = st.selectbox(
                "Filter by quality:",
                ["All", "High (8+)", "Medium (6-8)", "Low (<6)"]
            )

        filtered = convs
        if intent_filter != "All":
            filtered = [c for c in filtered if c["intent"] == intent_filter]
        if quality_filter == "High (8+)":
            filtered = [c for c in filtered if c["overall_score"] >= 8]
        elif quality_filter == "Medium (6-8)":
            filtered = [c for c in filtered
                       if 6 <= c["overall_score"] < 8]
        elif quality_filter == "Low (<6)":
            filtered = [c for c in filtered if c["overall_score"] < 6]

        for conv in filtered:
            emoji = {
                "faq": "❓", "order": "📦",
                "refund": "💰", "escalate": "🚨",
                "complaint": "😡"
            }.get(conv["intent"], "💬")

            score = conv["overall_score"]
            quality_icon = "🟢" if score >= 8 else "🟡" if score >= 6 else "🔴"

            with st.expander(
                f"{emoji} {quality_icon} [{conv['timestamp']}] "
                f"{conv['message'][:50]}... "
                f"| Quality: {score}/10"
            ):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Customer:** {conv['message']}")
                with col2:
                    st.write(f"**Agent:** {conv['agent_used']} "
                            f"| Intent: {conv['intent']} "
                            f"| Time: {conv['response_time']}s")

                st.write(f"**Response:** {conv['response']}")
                st.divider()

                # Eval scores
                c1, c2, c3, c4, c5 = st.columns(5)
                with c1:
                    st.metric("Overall", f"{conv['overall_score']}/10")
                with c2:
                    st.metric("Relevance", f"{conv['relevance_score']}/10")
                with c3:
                    st.metric("Tone", f"{conv['tone_score']}/10")
                with c4:
                    st.metric("Resolution", f"{conv['resolution_score']}/10")
                with c5:
                    st.metric("Routing", f"{conv['routing_score']}/10")

                # Eval reasons
                # Eval reasons
                st.markdown("**Eval Reasoning:**")
                st.write(f"• Relevance: {conv['relevance_reason']}")
                st.write(f"• Tone: {conv['tone_reason']}")
                st.write(f"• Resolution: {conv['resolution_reason']}")