from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.session import SessionLocal
from app.api.sqlsafe import TEMPLATES  # reuse your whitelist
from app.services.llm_client import chat, extract_json

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class AskSqlRequest(BaseModel):
    question: str = Field(..., description="Coach natural-language question")

SYSTEM_PROMPT = """You classify a coach's question into one SQL template and fill params.
Allowed templates:
- whiff_rate_by_pitcher(params: pitcher:str)
- recent_pitches_by_pitcher(params: pitcher:str, limit:int)

Respond ONLY as JSON:
{"template":"<name>","params":{"pitcher":"...", "limit": 20},"reason":"<short why>"}"""

def _coerce_and_validate(template: str, params: Dict[str, Any]) -> Dict[str, Any]:
    tpl = TEMPLATES.get(template)
    if not tpl:
        raise HTTPException(status_code=400, detail=f"Unknown template: {template}")
    coerced: Dict[str, Any] = {}
    for p_name, p_type in tpl["params"].items():
        if p_name not in params:
            raise HTTPException(status_code=400, detail=f"Missing param: {p_name}")
        try:
            val = p_type(params[p_name])
        except Exception:
            raise HTTPException(status_code=400, detail=f"Param {p_name} must be {p_type.__name__}")
        if isinstance(val, str):
            val = val.strip()
            if not val:
                raise HTTPException(status_code=400, detail=f"Param {p_name} cannot be empty")
        if p_name == "limit":
            val = max(1, min(int(val), 500))
        coerced[p_name] = val
    return coerced

def _execute_template(db: Session, template: str, params: Dict[str, Any]) -> Dict[str, Any]:
    tpl = TEMPLATES[template]
    rows = db.execute(text(tpl["sql"]), params).mappings().all()
    if tpl["returns"] == "rows":
        return {"rows": list(rows)}
    if tpl["returns"] == "stat":
        if not rows:
            return {"result": None}
        r = rows[0]
        swings = int(r.get("swings") or 0)
        whiffs = int(r.get("whiffs") or 0)
        rate = (whiffs / swings) if swings else None
        return {"result": {"pitcher": params.get("pitcher"), "swings": swings, "whiffs": whiffs, "whiff_rate": rate}}
    return {"rows": list(rows)}

def _heuristic_fallback(question: str) -> Optional[Dict[str, Any]]:
    """Very tiny rule-based fallback if no LLM configured or it fails."""
    q = question.lower()
    # Guess pitcher: last word after "for " if present
    pitcher = None
    if "for " in q:
        pitcher = q.split("for ", 1)[1].strip().split()[0]
    # If mentions "recent" or "last", use recent_pitches_by_pitcher
    if "recent" in q or "last" in q:
        return {"template": "recent_pitches_by_pitcher", "params": {"pitcher": pitcher or "", "limit": 20}, "reason": "heuristic: recent"}
    # If mentions "whiff", use whiff_rate_by_pitcher
    if "whiff" in q:
        return {"template": "whiff_rate_by_pitcher", "params": {"pitcher": pitcher or ""}, "reason": "heuristic: whiff"}
    return None

@router.post("/ask")
def ask_sql(req: AskSqlRequest, db: Session = Depends(get_db)):

    model_resp = chat([
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": req.question}
    ])

    chosen = None
    source = "llm"
    if model_resp:
        parsed = extract_json(model_resp)
        if parsed and "template" in parsed and "params" in parsed:
            chosen = parsed

    if not chosen:
        fallback = _heuristic_fallback(req.question)
        if not fallback:
            raise HTTPException(status_code=400, detail="Could not classify question. Please mention the pitcher and whether you want whiff rate or recent pitches.")
        chosen = fallback
        source = "heuristic"

    template = chosen["template"]
    params = _coerce_and_validate(template, chosen["params"])
    result = _execute_template(db, template, params)

    return {
        "question": req.question,
        "chosen": {"template": template, "params": params, "source": source, "reason": chosen.get("reason", "")},
        "result": result,
        "raw_model_text": model_resp or None
    }
