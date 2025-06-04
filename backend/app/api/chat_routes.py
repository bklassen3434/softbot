from fastapi import APIRouter, Request
from app.services.langchain_service import run_chain

router = APIRouter()

@router.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_input = data.get("message")
    session_id = data.get("session_id", "default")  # Get session_id from request, default to "default"
    
    response = run_chain(user_input, session_id)
    return {"response": response}
