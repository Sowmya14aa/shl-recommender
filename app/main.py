"""
main.py — FastAPI application with two endpoints.

GET  /health  → readiness check
POST /chat    → main conversation endpoint

Run with:
    uvicorn app.main:app --reload
"""

from fastapi import FastAPI, HTTPException
from app.schemas import ChatRequest, ChatResponse, Recommendation
from app.chat_handler import handle_chat

app = FastAPI(
    title="SHL Assessment Recommender",
    description="Conversational agent for recommending SHL assessments",
    version="1.0.0"
)


@app.get("/health")
def health():
    """Readiness check — required by the assignment."""
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Main chat endpoint.

    Receives full conversation history.
    Returns assistant reply + optional recommendations.
    Stateless — no server-side session storage.
    """
    if not request.messages:
        raise HTTPException(status_code=400, detail="messages cannot be empty")

    # Convert Pydantic objects to plain dicts for internal processing
    messages = [{"role": m.role, "content": m.content} for m in request.messages]

    result = handle_chat(messages)

    return ChatResponse(
        reply                = result["reply"],
        recommendations      = result["recommendations"],
        end_of_conversation  = result["end_of_conversation"],
    )