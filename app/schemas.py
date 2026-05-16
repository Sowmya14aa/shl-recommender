"""
schemas.py — Pydantic models for request and response validation.

The assignment schema is NON-NEGOTIABLE.
Every response MUST follow this exact structure.
Pydantic enforces this automatically — if our code returns
the wrong shape, FastAPI raises an error before it reaches the user.
"""

from pydantic import BaseModel
from typing import List


class Message(BaseModel):
    """One turn in the conversation. Role is 'user' or 'assistant'."""
    role: str
    content: str


class ChatRequest(BaseModel):
    """What the client sends to POST /chat."""
    messages: List[Message]


class Recommendation(BaseModel):
    """One assessment in the shortlist."""
    name: str
    url: str
    test_type: str


class ChatResponse(BaseModel):
    """
    What we ALWAYS return from POST /chat.
    This schema is fixed by the assignment — never change the field names.

    - reply: the assistant's message to the user
    - recommendations: empty list when clarifying, 1-10 items when recommending
    - end_of_conversation: True only when the task is fully complete
    """
    reply: str
    recommendations: List[Recommendation] = []
    end_of_conversation: bool = False