Full-stack app for uploading softball pitch data and asking questions via LLM → SQL.  
Stack: **React (Vite+TS)** + **FastAPI** + **Postgres** (Docker) + **OpenAI-compatible** LLM (e.g., LLama3-8B).

---

## Repo layout

.
├─ backend/ # FastAPI app, SQL validator, safe SQL templates
├─ frontend/ # React app (Vite + TypeScript)
├─ models/ # local model weights/configs for Ollama
├─ docker-compose.yml
└─ README.md


---

## Prereqs

- Docker Desktop (or Docker + Compose)
- Node.js ≥ 18 (for local FE dev)
- Local LLM server (Ollama with OpenAI-compatible `/v1`)

---

## Quickstart

```bash
docker compose up --build

Open:

Frontend: http://localhost:5173

API: http://localhost:8000/health

---

Env (API)

Set in docker-compose.yml → services.api.environment:

DATABASE_URL (defaults to Compose Postgres)

LLM_BASE_URL (e.g. http://host.docker.internal:11434/v1 for Ollama)

LLM_MODEL_NAME

LLM_API_KEY (if required)

LLM_RATE_MAX (default 30)

LLM_RATE_WINDOW_SEC (default 3600)

---

CSV format

Headers must be exact:

game_date,pitcher,batter,pitch_type,result

Upload via UI or:

curl -X POST http://localhost:8000/pitches/upload-csv \
  -F "file=@sample.csv"

---

Key endpoints

GET /health

POST /pitches/upload-csv (size/row-capped, bulk insert)

POST /sql/freeform/ask (LLM writes SQL → validator → execute; rate-limited)

---

CURL example

curl -sS -X POST http://localhost:8000/sql/freeform/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Count pitches by pitch_type for Smith, most to least"}' | jq

---

Troubleshooting

CORS: ensure backend allows http://localhost:5173

429: you hit LLM rate limit; tune env

Upload 400: check headers / size / row caps

Freeform 400: validator blocked joins/subqueries/unsupported functions

