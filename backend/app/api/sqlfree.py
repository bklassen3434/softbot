from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.services.rate_limit import llm_rate_limit

from app.db.session import SessionLocal
from app.services.llm_client import chat, extract_json
from app.services.sql_validation import validate_and_rewrite_sql, ValidationError

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class FreeformAskRequest(BaseModel):
    question: str = Field(..., description="Coach question in natural language")

SYSTEM_PROMPT = """You are an assistant that writes a single safe SQL SELECT for Postgres
against this schema:

TABLE pitches(id, game_date, pitcher, batter, pitch_type, result)

Rules:
- Select only from pitches (single table)
- Allowed aggregates: COUNT, SUM, AVG, MIN, MAX
- If mixing aggregates with columns, include proper GROUP BY columns
- ORDER BY may reference columns, select aliases, or aggregates
- No JOINs or subqueries
- Always include a numeric LIMIT (<= 100 by default)
- Prefer named parameters with :param (e.g., WHERE pitcher = :pitcher)

Return ONLY JSON:
{"sql":"SELECT pitch_type, COUNT(*) AS n FROM pitches WHERE pitcher = :pitcher GROUP BY pitch_type ORDER BY n DESC LIMIT 25","params":{"pitcher":"Smith"}}"""


@router.post("/freeform/ask", dependencies=[Depends(llm_rate_limit)])
def freeform_ask(req: FreeformAskRequest, db: Session = Depends(get_db)):
    # 1) Ask the model to propose SQL + params as JSON
    model_text = chat([
        {"role":"system", "content": SYSTEM_PROMPT},
        {"role":"user", "content": req.question}
    ], max_tokens=300)

    if not model_text:
        raise HTTPException(status_code=502, detail="LLM did not respond")

    parsed = extract_json(model_text)
    if not parsed or "sql" not in parsed:
        raise HTTPException(status_code=400, detail="LLM response not understood")

    sql = str(parsed["sql"])
    params: Dict[str, Any] = parsed.get("params", {}) or {}

    # 2) Validate / rewrite SQL
    try:
        safe_sql = validate_and_rewrite_sql(sql)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=f"SQL not allowed: {e}")

    # 3) Execute
    try:
        rows = db.execute(text(safe_sql), params).mappings().all()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"SQL execution error: {e}")

    return {
        "question": req.question,
        "proposed_sql": sql,
        "safe_sql": safe_sql,
        "params": params,
        "rows": list(rows),
        "raw_model_text": model_text
    }
