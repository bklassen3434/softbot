from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import time
from app.api import pitches
from app.api import sqlsafe
from app.api import sqlask
from app.api import sqlfree


app = FastAPI(title="Softball Assistant API", version="0.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True}

app.include_router(pitches.router, prefix="/pitches", tags=["pitches"])
app.include_router(safe_sql_router := sqlsafe.router, prefix="/sql", tags=["sql"])
app.include_router(sqlask.router, prefix="/sql", tags=["sql"])
app.include_router(sqlfree.router, prefix="/sql", tags=["sql"])