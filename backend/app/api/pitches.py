from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session
from datetime import datetime
import csv, io, os

from app.db.session import SessionLocal, engine
from app.models.base import Base
from app.models.pitch import Pitch
from app.schemas.pitch import PitchIn, PitchOut

router = APIRouter()

# Create tables at import time (simple for MVP)
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("", response_model=PitchOut)
def create_pitch(pitch: PitchIn, db: Session = Depends(get_db)):
    obj = Pitch(**pitch.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@router.get("", response_model=List[PitchOut])
def list_pitches(limit: int = 50, db: Session = Depends(get_db)):
    rows = db.query(Pitch).order_by(Pitch.id.desc()).limit(limit).all()
    return rows

@router.post("/upload-csv")
async def upload_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Accepts a CSV with headers: game_date,pitcher,batter,pitch_type,result
    Example row:
      2024-04-12,Smith,Jones,slider,swing_miss

    Caps:
    - file size: MAX_UPLOAD_MB (env, default 5 MB)
    - row count: MAX_UPLOAD_ROWS (env, default 50000)
    Uses SQLAlchemy bulk insert for speed.
    """

    MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "5"))
    MAX_UPLOAD_ROWS = int(os.getenv("MAX_UPLOAD_ROWS", "50000"))

    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a .csv file")

    raw = await file.read()
    size_mb = len(raw) / (1024 * 1024)
    if size_mb > MAX_UPLOAD_MB:
        raise HTTPException(
            status_code=413,
            detail=f"File too large: {size_mb:.2f} MB (max {MAX_UPLOAD_MB} MB)."
        )

    text = raw.decode("utf-8", errors="ignore")
    reader = csv.DictReader(io.StringIO(text))

    required = {"game_date", "pitcher", "batter", "pitch_type", "result"}
    if set(reader.fieldnames or []) != required:
        raise HTTPException(
            status_code=400,
            detail=f"CSV must have EXACT columns: {','.join(sorted(required))}"
        )

    objects = []
    capped = False
    for i, row in enumerate(reader, start=1):
        if i > MAX_UPLOAD_ROWS:
            capped = True
            break
        try:
            objects.append(Pitch(
                game_date=datetime.strptime(row["game_date"].strip(), "%Y-%m-%d").date(),
                pitcher=row["pitcher"].strip(),
                batter=row["batter"].strip(),
                pitch_type=row["pitch_type"].strip(),
                result=row["result"].strip(),
            ))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Bad row #{i}: {row}. Error: {e}")

    # ---- BULK INSERT ----
    if objects:
        db.bulk_save_objects(objects)  # fast path
        db.commit()

    return {"ok": True, "inserted": len(objects), "capped": capped}

