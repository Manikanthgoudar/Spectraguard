from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.user import User
from app.models.chat_message import ChatMessage
from app.core.dependencies import get_current_user
from app.services.gemini_service import get_gemini_reply

router = APIRouter(prefix="/chat", tags=["Chat"])


class MessageRequest(BaseModel):
    message: str


class MessageResponse(BaseModel):
    id: int
    sender: str
    text: str
    created_at: str

    class Config:
        from_attributes = True


@router.get("/messages", response_model=List[MessageResponse])
def get_chat_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves isolated chat history for the authenticated user."""
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == current_user.id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )

    return [
        MessageResponse(
            id=m.id,
            sender=m.sender,
            text=m.text,
            created_at=m.created_at.isoformat(),
        )
        for m in messages
    ]


@router.post("/message", response_model=MessageResponse)
def send_chat_message(
    payload: MessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Sends a chat message to Gemini AI and returns the reply, isolated to current user."""
    user_text = payload.message.strip()
    if not user_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty",
        )

    # 1. Save user message
    user_msg = ChatMessage(
        user_id=current_user.id,
        sender="user",
        text=user_text,
    )
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    # 2. Generate Gemini reply
    bot_reply_text = get_gemini_reply(user_text)

    # 3. Save bot message
    bot_msg = ChatMessage(
        user_id=current_user.id,
        sender="bot",
        text=bot_reply_text,
    )
    db.add(bot_msg)
    db.commit()
    db.refresh(bot_msg)

    return MessageResponse(
        id=bot_msg.id,
        sender=bot_msg.sender,
        text=bot_msg.text,
        created_at=bot_msg.created_at.isoformat(),
    )


@router.delete("/messages")
def clear_chat_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Clears chat history for the authenticated user only."""
    db.query(ChatMessage).filter(ChatMessage.user_id == current_user.id).delete()
    db.commit()
    return {"message": "Chat history cleared successfully."}
