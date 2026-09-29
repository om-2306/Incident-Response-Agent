# ⚡ AI Incident Response Agent (HackwithHyderabad 3.0)

An autonomous AI Incident Response & SRE Agent powered by **Hindsight** (by Vectorize) for persistent episodic memory and **Groq API** for fast LLM inference.

---

## 🎯 Architecture Overview

When a production outage occurs, DevOps teams spend hours diagnosing cryptic error logs that have often been solved before. This agent leverages **Hindsight Episodic Memory** to recall past incident root causes and resolutions, allowing it to instantly prescribe exact terminal commands and config fixes for recurring or similar production errors.

```
       [Raw Production Log Input]
                   │
                   ▼
     🧠 Hindsight Episodic Memory
   (Semantic Recall of Past Incidents)
                   │
                   ▼
       ⚡ Groq LLM (SRE Engine)
 (Generates Root Cause + Fix Commands)
                   │
                   ▼
   💾 Interactive Memory Retention
(Saves Verified Fix back into Hindsight)
```

---

## 🚀 Key Features

1. **Episodic Memory Layer (Hindsight SDK)**:
   - Uses `hindsight-client` to retain and recall past incident memories.
   - Includes fallback resilience to ensure local zero-downtime performance during hackathon live demos.
2. **Judge-Facing Memory Visibility**:
   - Streamlit UI includes an explicit `st.expander("🧠 Agent Memory (Hindsight)")` displaying recalled past incidents, match confidence, root cause, and past resolutions *before* generating answers.
3. **Fast SRE Inference (Groq LLM)**:
   - Uses `llama-3.3-70b-versatile` / `qwen-2.5-32b` for rapid diagnosis and shell command generation.
4. **Interactive Memory Retention ("Mark as Resolved")**:
   - User can confirm or edit the final resolution, which is saved back into Hindsight episodic memory with 1 click.
5. **Pre-Seeded Synthetic Incidents**:
   - `seed_data.py` pre-populates 5 realistic production outages (Database pool timeouts, Redis OOM storm, Kafka lag, ALB 502, Elasticsearch red cluster).

---

## ⚙️ Installation & Setup

### 1. Prerequisites
- Python 3.10+
- Pip package manager

### 2. Clone Repository & Install Dependencies
```bash
# Install required Python packages
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your API keys:
```env
HINDSIGHT_API_KEY=your_hindsight_api_key_here
HINDSIGHT_BASE_URL=https://api.hindsight.vectorize.io
HINDSIGHT_BANK_ID=hackathon-incident-response

GROQ_API_KEY=your_groq_api_key_here
```
*(Note: If API keys are not set, the agent automatically runs in resilient local memory mode for offline demos.)*

---

## 🧪 Running the Demo

### Step 1: Seed Hindsight Memory Database
Run the seed script to push the 5 synthetic production incidents into Hindsight memory:
```bash
python seed_data.py
```

### Step 2: Launch Streamlit UI
Run the Streamlit web app:
```bash
python -m streamlit run app.py
```

Open your browser at `http://localhost:8501`.

---

## 📁 Project Structure

```
├── app.py                   # Streamlit Web Application UI
├── memory.py                # Hindsight SDK Client & Episodic Memory Manager
├── llm.py                   # Groq LLM Engine & SRE System Prompts
├── seed_data.py             # Synthetic Seed Script (5 Realistic Production Incidents)
├── incident_memory_store.json # Persistent Local Backup Memory Store
├── requirements.txt         # Project Dependencies
├── .env.example             # Environment Variables Template
└── README.md                # Documentation
```

---

## 🏆 HackwithHyderabad 3.0 Judging Criteria Compliance

| Requirement | Implementation |
|---|---|
| **Memory Layer** | Integrated `hindsight-client` with `retain()` and `recall()` methods. |
| **UI Memory Visibility** | `st.expander("🧠 Agent Memory (Hindsight)")` shows top 3 recalled memories with relevance scores and root causes. |
| **Seed Incidents** | 5 realistic synthetic incidents seeded via `seed_data.py`. |
| **LLM Provider** | Groq API fast inference integration in `llm.py`. |
| **Interactive Retention** | "Save as Episodic Memory to Hindsight" button writes new incidents to Hindsight. |
