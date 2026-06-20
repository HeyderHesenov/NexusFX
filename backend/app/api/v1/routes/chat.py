"""AI Asistant chat route — finance advisor (ikili AI debate)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.advisor import answer
from app.db.session import get_db

router = APIRouter()


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    lang: str = "az"


class ChatResponse(BaseModel):
    answer: str
    refused: bool = False


@router.post("", response_model=ChatResponse)
async def chat(
    req: ChatRequest, db: AsyncSession = Depends(get_db)
) -> ChatResponse:
    """İstifadəçi sualına maliyyə cavabı (arxa fonda debate)."""
    result = await answer(req.message, req.lang, db)
    return ChatResponse(**result)
