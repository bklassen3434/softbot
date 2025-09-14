import os, json, re
import httpx
from typing import Dict, Any, Optional, List
from app.settings import settings
LLM_BASE_URL = settings.LLM_BASE_URL
LLM_API_KEY = settings.LLM_API_KEY
LLM_MODEL_NAME = settings.LLM_MODEL_NAME

# LLM_BASE_URL = os.getenv("LLM_BASE_URL", "")
# LLM_API_KEY  = os.getenv("LLM_API_KEY", "")
# LLM_MODEL    = os.getenv("LLM_MODEL_NAME")

def _headers():
    h = {"Content-Type": "application/json"}
    if LLM_API_KEY:
        h["Authorization"] = f"Bearer {LLM_API_KEY}"
    return h

def chat(messages: List[Dict[str, str]], max_tokens: int = 400) -> Optional[str]:
    """Call an OpenAI-compatible /v1/chat/completions endpoint. Returns the message content or None on failure."""
    if not LLM_BASE_URL:
        return None
    try:
        r = httpx.post(
            f"{LLM_BASE_URL}/chat/completions",
            headers=_headers(),
            json={"model": LLM_MODEL_NAME, "messages": messages, "temperature": 0, "max_tokens": max_tokens},
            timeout=30.0,
        )
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"]
    except Exception:
        return None

def extract_json(text: str) -> Optional[Dict[str, Any]]:
    """Grab the first {...} block and parse as JSON."""
    if not text:
        return None
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except Exception:
        return None
