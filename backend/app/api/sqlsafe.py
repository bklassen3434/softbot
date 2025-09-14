from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.session import SessionLocal

router = APIRouter()

# --- DB session dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Whitelist of allowed SQL templates (no string concatenation!) ---
TEMPLATES = {
    "whiff_rate_by_pitcher": {
        "sql": """
            SELECT
              SUM(CASE WHEN result IN ('swing_miss','foul','in_play') THEN 1 ELSE 0 END) AS swings,
              SUM(CASE WHEN result = 'swing_miss' THEN 1 ELSE 0 END) AS whiffs
            FROM pitches
            WHERE pitcher = :pitcher
        """,
        "params": {"pitcher": str},
        "returns": "stat",
    },
    "recent_pitches_by_pitcher": {
        "sql": """
            SELECT id, game_date, pitcher, batter, pitch_type, result
            FROM pitches
            WHERE pitcher = :pitcher
            ORDER BY id DESC
            LIMIT :limit
        """,
        "params": {"pitcher": str, "limit": int},
        "returns": "rows",
    },
}

class SqlRunRequest(BaseModel):
    template: str = Field(..., description="One of: " + ", ".join(TEMPLATES.keys()))
    params: Dict[str, Any] = Field(default_factory=dict)

@router.post("/run")
def run_sql(req: SqlRunRequest, db: Session = Depends(get_db)):

    tpl = TEMPLATES.get(req.template)
    if not tpl:
        raise HTTPException(status_code=400, detail=f"Unknown template: {req.template}")

    coerced: Dict[str, Any] = {}
    for p_name, p_type in tpl["params"].items():
        if p_name not in req.params:
            raise HTTPException(status_code=400, detail=f"Missing param: {p_name}")
        val = req.params[p_name]

        try:
            coerced_val = p_type(val)
        except Exception:
            raise HTTPException(status_code=400, detail=f"Param {p_name} must be {p_type.__name__}")

        if isinstance(coerced_val, str):
            coerced_val = coerced_val.strip()
            if len(coerced_val) == 0:
                raise HTTPException(status_code=400, detail=f"Param {p_name} cannot be empty")
        if p_name == "limit":

            coerced_val = max(1, min(int(coerced_val), 500))
        coerced[p_name] = coerced_val

    rows = db.execute(text(tpl["sql"]), coerced).mappings().all()

    # 4) Post-process
    if tpl["returns"] == "rows":
        return {"template": req.template, "rows": list(rows)}
    elif tpl["returns"] == "stat":
        if not rows:
            return {"template": req.template, "result": None}
        r = rows[0]
        swings = int(r.get("swings") or 0)
        whiffs = int(r.get("whiffs") or 0)
        rate = (whiffs / swings) if swings else None
        # include any inputs in the response for clarity
        out = {"pitcher": coerced.get("pitcher"), "swings": swings, "whiffs": whiffs, "whiff_rate": rate}
        return {"template": req.template, "result": out}
    else:
        return {"template": req.template, "rows": list(rows)}
