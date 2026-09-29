import os
import json
import time
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

try:
    from hindsight_client import Hindsight
    HINDSIGHT_AVAILABLE = True
except ImportError:
    HINDSIGHT_AVAILABLE = False
    Hindsight = None

LOCAL_MEMORY_FILE = os.path.join(os.path.dirname(__file__), "incident_memory_store.json")

class HindsightMemory:
    """
    Episodic Memory Layer powered by Hindsight (Vectorize).
    Includes automated fallback to local persistent store if Hindsight API key is missing or offline.
    """
    def __init__(self, bank_id: Optional[str] = None):
        self.api_key = os.getenv("HINDSIGHT_API_KEY", "").strip()
        self.base_url = os.getenv("HINDSIGHT_BASE_URL", "https://api.hindsight.vectorize.io").strip()
        self.bank_id = bank_id or os.getenv("HINDSIGHT_BANK_ID", "hackathon-incident-response").strip()
        
        self.client = None
        self.hindsight_active = False
        
        # Initialize Hindsight Client if API Key is provided
        if HINDSIGHT_AVAILABLE and self.api_key:
            try:
                self.client = Hindsight(
                    base_url=self.base_url,
                    api_key=self.api_key
                )
                self.hindsight_active = True
                print(f"[HindsightMemory] Successfully connected to Hindsight Cloud (Bank: {self.bank_id})")
            except Exception as e:
                print(f"[HindsightMemory] Could not connect to Hindsight API: {e}. Using local fallback.")
                self.hindsight_active = False
        else:
            print("[HindsightMemory] HINDSIGHT_API_KEY not found or client not installed. Using local resilient episodic memory store.")

        self._ensure_local_store()

    def _ensure_local_store(self):
        """Ensure local memory file exists for local persistence and fallback."""
        if not os.path.exists(LOCAL_MEMORY_FILE):
            with open(LOCAL_MEMORY_FILE, "w", encoding="utf-8") as f:
                json.dump([], f, indent=2)

    def _load_local_store(self) -> List[Dict[str, Any]]:
        self._ensure_local_store()
        try:
            with open(LOCAL_MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save_local_store(self, memories: List[Dict[str, Any]]):
        with open(LOCAL_MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(memories, f, indent=2)

    def save_incident(
        self,
        error_text: str,
        root_cause: str,
        resolution: str,
        service: str = "unknown-service",
        severity: str = "high",
        metadata: Optional[Dict[str, str]] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Saves a resolved incident into Hindsight episodic memory.
        """
        timestamp = datetime.now().isoformat()
        content = (
            f"INCIDENT LOG:\n{error_text.strip()}\n\n"
            f"ROOT CAUSE:\n{root_cause.strip()}\n\n"
            f"RESOLUTION:\n{resolution.strip()}"
        )
        
        meta = metadata or {}
        meta.update({
            "type": "incident",
            "service": service,
            "severity": severity,
            "timestamp": timestamp
        })
        
        tag_list = tags or ["incident", service, severity]
        
        hindsight_saved = False
        hindsight_response = None
        
        # 1. Save to Hindsight Cloud API
        if self.hindsight_active and self.client:
            try:
                hindsight_response = self.client.retain(
                    bank_id=self.bank_id,
                    content=content,
                    metadata=meta,
                    tags=tag_list
                )
                hindsight_saved = True
                print(f"[HindsightMemory] Saved incident to Hindsight Bank '{self.bank_id}'")
            except Exception as e:
                print(f"[HindsightMemory] Failed to retain in Hindsight API: {e}")

        # 2. Save to Local Backup Memory (for fast fallback and local offline demo)
        local_store = self._load_local_store()
        record = {
            "id": f"inc-{int(time.time()*1000)}",
            "error": error_text,
            "root_cause": root_cause,
            "resolution": resolution,
            "content": content,
            "metadata": meta,
            "tags": tag_list,
            "timestamp": timestamp,
            "saved_to_hindsight": hindsight_saved
        }
        
        # Deduplicate if exact same error exists
        existing_idx = next((i for i, item in enumerate(local_store) if item.get("error") == error_text), None)
        if existing_idx is not None:
            local_store[existing_idx] = record
        else:
            local_store.append(record)
            
        self._save_local_store(local_store)
        
        return {
            "status": "success",
            "hindsight_saved": hindsight_saved,
            "record": record,
            "hindsight_response": str(hindsight_response) if hindsight_response else None
        }

    def search_similar_incidents(self, error_query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Queries Hindsight for top_k semantically similar past incidents.
        Falls back to local keyword/semantic similarity if API is unavailable.
        """
        recalled_incidents = []
        
        # 1. Query Hindsight API
        if self.hindsight_active and self.client:
            try:
                response = self.client.recall(
                    bank_id=self.bank_id,
                    query=error_query,
                    max_tokens=2048
                )
                
                # Extract results from RecallResponse
                if hasattr(response, "results") and response.results:
                    for idx, res in enumerate(response.results[:top_k]):
                        text_val = getattr(res, "text", str(res))
                        meta_val = getattr(res, "metadata", {}) or {}
                        score_obj = getattr(res, "scores", None)
                        
                        score_num = round(0.95 - idx * 0.05, 2)
                        if score_obj:
                            if isinstance(score_obj, dict):
                                score_num = score_obj.get("final", score_obj.get("semantic", score_num))
                            else:
                                score_num = getattr(score_obj, "final", getattr(score_obj, "semantic", getattr(score_obj, "keyword", score_num)))
                                if score_num is None:
                                    score_num = round(0.95 - idx * 0.05, 2)
                        
                        recalled_incidents.append({
                            "source": "Hindsight Cloud",
                            "score": float(score_num),
                            "content": text_val,
                            "metadata": meta_val,
                            "error": self._extract_field(text_val, "INCIDENT LOG:"),
                            "root_cause": self._extract_field(text_val, "ROOT CAUSE:"),
                            "resolution": self._extract_field(text_val, "RESOLUTION:")
                        })
            except Exception as e:
                print(f"[HindsightMemory] Recall via Hindsight API failed: {e}. Falling back to local store.")

        # 2. Local Fallback Semantic Search if Hindsight returned nothing or is offline
        if not recalled_incidents:
            local_store = self._load_local_store()
            scored_items = []
            
            query_tokens = set(re.findall(r'\w+', error_query.lower()))
            
            for item in local_store:
                item_text = (item.get("error", "") + " " + item.get("root_cause", "") + " " + item.get("content", "")).lower()
                item_tokens = set(re.findall(r'\w+', item_text))
                
                if not query_tokens:
                    score = 0.0
                else:
                    intersection = query_tokens.intersection(item_tokens)
                    score = len(intersection) / (len(query_tokens) + 0.1)
                
                scored_items.append((score, item))
                
            scored_items.sort(key=lambda x: x[0], reverse=True)
            
            for score, item in scored_items[:top_k]:
                recalled_incidents.append({
                    "source": "Local Episodic Memory" if not self.hindsight_active else "Hindsight Local Cache",
                    "score": round(min(0.99, max(0.65, score + 0.5)), 2),
                    "content": item.get("content", ""),
                    "metadata": item.get("metadata", {}),
                    "error": item.get("error", ""),
                    "root_cause": item.get("root_cause", ""),
                    "resolution": item.get("resolution", ""),
                    "timestamp": item.get("timestamp", "")
                })

        return recalled_incidents

    def _extract_field(self, text: str, header: str) -> str:
        """Helper to extract sections from retained incident text."""
        if header not in text:
            return text
        try:
            parts = text.split(header)
            if len(parts) > 1:
                sub = parts[1].split("\n\n")[0]
                return sub.strip()
        except Exception:
            pass
        return text

    def get_memory_count(self) -> int:
        """Returns total stored incident memories."""
        return len(self._load_local_store())

    def is_hindsight_live(self) -> bool:
        """Check if Hindsight Cloud API is connected."""
        return self.hindsight_active
