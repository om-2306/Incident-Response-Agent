import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    Groq = None

# List of models in order of preference for fast inference
GROQ_MODELS = [
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "llama-3.3-70b-versatile",
    "qwen/qwen3-32b",
    "llama-3.3-70b"
]

SYSTEM_PROMPT = """You are a Principal DevOps & Site Reliability Engineer (SRE) specializing in automated production incident response.

You have access to historical episodic memory of past production incidents (retrieved via Hindsight episodic memory).

Your goal:
1. Analyze the raw production error log provided by the user.
2. Compare it against the recalled past incidents from Hindsight episodic memory.
3. Provide a clear, actionable diagnosis and resolution guide.

Structure your response using Markdown with the following exact sections:
### 🔍 1. Root Cause Analysis
Explain clearly what went wrong based on error log signatures and historical parallels.

### 🧠 2. Historical Memory Context
Reference the relevant past incidents retrieved from Hindsight and how their root causes and resolutions apply to this current incident.

### 🛠️ 3. Recommended Remediation Commands
Provide copy-pasteable terminal commands (kubectl, docker, psql, redis-cli, systemctl, etc.) or config snippet changes needed to resolve the incident IMMEDIATELY.

### 🛡️ 4. Long-Term Prevention
Suggest architectural or monitoring improvements to prevent recurrence.
"""

def generate_diagnosis(current_error: str, historical_incidents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generates diagnosis and resolution using Groq LLM enriched with Hindsight historical incident context.
    """
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    
    # Format historical context for prompt
    context_str = ""
    if historical_incidents:
        context_str += "=== RECALLED PAST INCIDENTS FROM HINDSIGHT EPISODIC MEMORY ===\n"
        for idx, inc in enumerate(historical_incidents, 1):
            source = inc.get("source", "Hindsight Memory")
            score = inc.get("score", 0.90)
            err = inc.get("error", inc.get("content", ""))
            cause = inc.get("root_cause", "N/A")
            res = inc.get("resolution", "N/A")
            
            context_str += (
                f"\n[Past Incident #{idx}] (Relevance Score: {score}, Source: {source})\n"
                f"Error: {err}\n"
                f"Root Cause: {cause}\n"
                f"Resolution: {res}\n"
            )
        context_str += "\n============================================================\n"
    else:
        context_str = "No directly matching past incidents found in memory.\n"

    user_prompt = (
        f"{context_str}\n"
        f"=== CURRENT RAW PRODUCTION ERROR LOG ===\n"
        f"{current_error.strip()}\n"
        f"========================================\n\n"
        f"Please synthesize the historical incident memory above and provide step-by-step remediation."
    )

    if GROQ_AVAILABLE and api_key:
        client = Groq(api_key=api_key)
        
        last_exception = None
        for model in GROQ_MODELS:
            try:
                print(f"[LLMEngine] Querying Groq API with model '{model}'...")
                completion = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.2,
                    max_tokens=2048
                )
                response_text = completion.choices[0].message.content
                print(f"[LLMEngine] Successfully generated response using model '{model}'")
                return {
                    "status": "success",
                    "model_used": model,
                    "response": response_text,
                    "is_fallback": False
                }
            except Exception as e:
                print(f"[LLMEngine] Model '{model}' failed: {e}")
                last_exception = e
                continue

    # Fallback generator if Groq API key is missing or fails
    return _generate_fallback_diagnosis(current_error, historical_incidents)


def _generate_fallback_diagnosis(current_error: str, historical_incidents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Resilient offline/fallback diagnosis generator in case GROQ_API_KEY is not configured yet.
    """
    top_inc = historical_incidents[0] if historical_incidents else None
    
    past_ref = ""
    if top_inc:
        past_ref = (
            f"**Recalled Incident Match:** `{top_inc.get('error', 'Similar Past Incident')}`\n"
            f"- **Historical Root Cause:** {top_inc.get('root_cause', 'Config or resource bottleneck')}\n"
            f"- **Historical Resolution:** {top_inc.get('resolution', 'Restart service and adjust configuration parameters.')}"
        )
    else:
        past_ref = "No historical match found. Generating standard SRE incident response workflow."

    fallback_text = f"""### 🔍 1. Root Cause Analysis
Based on the error signature in the current log:
> `{current_error[:120]}...`

The primary failure mode appears to be a **service bottleneck / resource starvation or connection failure** matching patterns observed in production deployments.

### 🧠 2. Historical Memory Context (Hindsight Recall)
{past_ref}

The symptoms indicate strong structural similarity to past incident patterns stored in Hindsight memory. Leveraging historical resolutions avoids manual trial and error.

### 🛠️ 3. Recommended Remediation Commands
Execute the following step-by-step resolution in your terminal/cluster:

```bash
# Step 1: Check pod/container health and resource limits
kubectl get pods -A | grep -E "Error|CrashLoopBackOff|OOMKilled"
kubectl describe pod -l app=service-name

# Step 2: Apply emergency configuration fix / resource ceiling expansion
kubectl scale deployment/service-name --replicas=3
kubectl rollout restart deployment/service-name

# Step 3: Verify connectivity and recovery
kubectl logs -f -l app=service-name --tail=50
```

### 🛡️ 4. Long-Term Prevention
1. **Automated Hindsight Memory Tagging:** Tag all similar incidents automatically to refine memory resolution precision over time.
2. **Prometheus Alertmanager Rules:** Configure latency and pool utilization alerts at 80% threshold.
"""
    return {
        "status": "success",
        "model_used": "Groq SRE Engine (Local Mode)",
        "response": fallback_text,
        "is_fallback": True
    }
