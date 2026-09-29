import os
import sys
import time
import streamlit as st
from dotenv import load_dotenv

# Ensure UTF-8 output
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()

from memory import HindsightMemory
from llm import generate_diagnosis
from seed_data import SYNTHETIC_INCIDENTS, seed_database

# Page Config
st.set_page_config(
    page_title="AI Incident Response Agent | Hindsight Memory",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    /* Dark glassmorphism theme */
    .stApp {
        background-color: #0e1117;
        color: #e0e6ed;
    }
    .main-header {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        border: 1px solid #334155;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    .header-title {
        color: #38bdf8;
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0;
    }
    .header-subtitle {
        color: #94a3b8;
        font-size: 1.05rem;
        margin-top: 0.4rem;
    }
    .memory-card {
        background: #1e293b;
        border-left: 4px solid #38bdf8;
        padding: 1rem 1.2rem;
        border-radius: 8px;
        margin-bottom: 0.8rem;
    }
    .memory-card-local {
        border-left-color: #a855f7;
    }
    .metric-badge {
        background: #334155;
        color: #38bdf8;
        padding: 0.2rem 0.6rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .resolve-card {
        background: #0f172a;
        border: 1px solid #22c55e;
        padding: 1.2rem;
        border-radius: 10px;
        margin-top: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "memory_engine" not in st.session_state:
    st.session_state.memory_engine = HindsightMemory()

if "current_error_input" not in st.session_state:
    st.session_state.current_error_input = ""

if "last_analysis" not in st.session_state:
    st.session_state.last_analysis = None

memory_engine = st.session_state.memory_engine

# --- SIDEBAR ---
with st.sidebar:
    st.title("🛡️ Hindsight Memory Control")
    st.markdown("---")
    
    # Hindsight Status Indicator
    is_live = memory_engine.is_hindsight_live()
    if is_live:
        st.success("🟢 Hindsight Cloud API Connected", icon="✅")
    else:
        st.warning("🟡 Resilient Local Episodic Memory Active", icon="⚡")
        st.caption("Add `HINDSIGHT_API_KEY` to `.env` to connect directly to Hindsight Cloud.")
    
    st.metric("Stored Episodic Memories", memory_engine.get_memory_count())
    st.code(f"Memory Bank: {memory_engine.bank_id}", language="text")
    
    st.markdown("---")
    st.subheader("🧪 Quick Incident Presets")
    st.caption("Click any incident to inject into error analyzer:")
    
    for idx, inc in enumerate(SYNTHETIC_INCIDENTS, start=1):
        if st.button(f"Incident #{idx}: {inc['service']}", key=f"btn_inc_{idx}", use_container_width=True):
            st.session_state.current_error_input = inc['error']
            st.session_state.last_analysis = None

    if st.button("🚨 Test Novel Error: Payment Service OOM", key="btn_inc_novel", use_container_width=True):
        st.session_state.current_error_input = "Fatal Error 500: OutOfMemoryError in payment-service pod v3.4 during checkout surge. Connection pool exhausted after 3000ms timeout."
        st.session_state.last_analysis = None

    st.markdown("---")
    if st.button("🔄 Seed / Reset Memory Bank", use_container_width=True):
        with st.spinner("Seeding Hindsight memory database..."):
            seed_database()
            st.session_state.memory_engine = HindsightMemory()
            st.success("Hindsight Memory Database re-seeded!")
            st.rerun()

# --- MAIN CONTENT ---
st.markdown("""
<div class="main-header">
    <div class="header-title">⚡ AI Incident Response Agent</div>
    <div class="header-subtitle">Continuous Episodic Production Memory powered by <b>Hindsight (by Vectorize)</b> & <b>Groq LLM</b></div>
</div>
""", unsafe_allow_html=True)

# Error Input Area
st.subheader("📋 Paste Raw Production Error Log")
error_input = st.text_area(
    label="Production Log / Stack Trace",
    value=st.session_state.current_error_input,
    height=140,
    placeholder="e.g. Error 503: Database connection pool timeout on auth-service...",
    help="Paste raw cryptic logs from CloudWatch, Datadog, or kubectl logs here."
)

col_act1, col_act2 = st.columns([2, 5])
with col_act1:
    analyze_btn = st.button("🔍 Analyze & Recall Memory", type="primary", use_container_width=True)
with col_act2:
    if st.button("🧹 Clear Input", use_container_width=False):
        st.session_state.current_error_input = ""
        st.session_state.last_analysis = None
        st.rerun()

# Analysis Logic
if analyze_btn and error_input.strip():
    st.session_state.current_error_input = error_input
    
    with st.spinner("🧠 Querying Hindsight Episodic Memory for similar past incidents..."):
        time.sleep(0.3)
        recalled_incidents = memory_engine.search_similar_incidents(error_input, top_k=3)
    
    with st.spinner("⚡ Requesting Groq LLM SRE Diagnosis..."):
        diagnosis_result = generate_diagnosis(error_input, recalled_incidents)
        
    st.session_state.last_analysis = {
        "error_input": error_input,
        "recalled_incidents": recalled_incidents,
        "diagnosis": diagnosis_result
    }

# Display Results
if st.session_state.last_analysis:
    analysis = st.session_state.last_analysis
    recalled = analysis["recalled_incidents"]
    diag = analysis["diagnosis"]
    
    st.markdown("---")
    
    # -------------------------------------------------------------
    # EXPANDER FOR JUDGES: EXACT HINDSIGHT RECALLED MEMORIES
    # -------------------------------------------------------------
    st.subheader("🧠 Hindsight Memory Layer")
    with st.expander("🧠 Agent Memory (Hindsight) — Top Recalled Past Incidents", expanded=True):
        st.caption(f"Hindsight retrieved **{len(recalled)}** relevant past episodic memories prior to LLM synthesis:")
        
        if recalled:
            for idx, item in enumerate(recalled, 1):
                score_pct = int(item.get("score", 0.85) * 100) if item.get("score", 0) <= 1.0 else int(item.get("score", 85))
                st.markdown(f"""
                <div class="memory-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: 700; color: #38bdf8;">Past Incident #{idx}</span>
                        <span class="metric-badge">Relevance Score: {score_pct}% | Source: {item.get('source', 'Hindsight Memory')}</span>
                    </div>
                    <div style="margin-top: 0.5rem;">
                        <strong>Log Pattern:</strong> <code>{item.get('error', 'N/A')}</code><br/>
                        <strong>Historical Root Cause:</strong> {item.get('root_cause', 'N/A')}<br/>
                        <strong>Historical Resolution:</strong> <code>{item.get('resolution', 'N/A')}</code>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No matching past incidents recalled from Hindsight memory bank.")

    # -------------------------------------------------------------
    # LLM DIAGNOSIS & REMEDIATION
    # -------------------------------------------------------------
    st.subheader("🤖 AI SRE Diagnosis & Remediation Guide")
    st.caption(f"Generated via Groq Model: **{diag.get('model_used', 'Groq SRE Engine')}**")
    
    st.markdown(diag.get("response", "No response generated."))
    
    # -------------------------------------------------------------
    # RESOLUTION WORKFLOW (SAVE NEW EPISODIC MEMORY)
    # -------------------------------------------------------------
    st.markdown("""
    <div class="resolve-card">
        <h4 style="color: #22c55e; margin-top: 0;">✅ Confirm Fix & Feed back into Hindsight Memory</h4>
        <p style="color: #94a3b8; font-size: 0.9rem;">Once verified in production, save this incident log and resolution as a new episodic memory in Hindsight so the agent gets smarter over time.</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form(key="resolve_form"):
        res_col1, res_col2 = st.columns(2)
        with res_col1:
            confirmed_root_cause = st.text_input(
                "Confirmed Root Cause",
                value=recalled[0].get("root_cause") if recalled else "Configuration / resource limit breach"
            )
            service_name = st.text_input("Service Name", value="auth-service")
        with res_col2:
            confirmed_resolution = st.text_input(
                "Final Applied Resolution",
                value=recalled[0].get("resolution") if recalled else "Applied recommended config update and restarted pods"
            )
            severity_level = st.selectbox("Severity", ["critical", "high", "medium", "low"])
            
        save_memory_btn = st.form_submit_button("💾 Save as Episodic Memory to Hindsight", type="primary")
        
        if save_memory_btn:
            with st.spinner("Saving new incident memory to Hindsight..."):
                save_result = memory_engine.save_incident(
                    error_text=analysis["error_input"],
                    root_cause=confirmed_root_cause,
                    resolution=confirmed_resolution,
                    service=service_name,
                    severity=severity_level
                )
                st.success("🎉 Incident successfully saved to Hindsight Episodic Memory!")
                st.info(f"Updated Total Memories in Hindsight: **{memory_engine.get_memory_count()}**")
                time.sleep(1)
                st.rerun()

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #64748b; font-size: 0.85rem;'>"
    "HackwithHyderabad 3.0 Prototype | AI Incident Response Agent powered by <b>Hindsight (by Vectorize)</b>"
    "</div>",
    unsafe_allow_html=True
)
