from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.services.agents.first_agent import run_first_agent
from app.dependencies.auth import get_current_user
from app.db.models.user import User
from app.core.checkpointer import get_checkpointer

router = APIRouter(prefix="/agent", tags=["Agent"])


class AgentRequest(BaseModel):
    query: str


class AgentResponse(BaseModel):
    response: str
    thread_id: str
    success: bool = True


# ==================== CHAT PRINCIPAL ====================
@router.post("/chat", response_model=AgentResponse)
async def chat_with_agent(
    request: AgentRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        thread_id = f"user_{current_user.firebase_uid}"

        response_text = await run_first_agent(
            query=request.query,
            thread_id=thread_id
        )

        return AgentResponse(
            response=response_text,
            thread_id=thread_id,
            success=True
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== CHAT TESTE ====================
@router.post("/chat-test", response_model=AgentResponse)
async def chat_with_agent_test(request: AgentRequest):
    try:
        thread_id = "test_user_123"

        response_text = await run_first_agent(
            query=request.query,
            thread_id=thread_id
        )

        return AgentResponse(
            response=response_text,
            thread_id=thread_id,
            success=True
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== HISTÓRICO ====================
@router.get("/history")
async def get_history(
    current_user: User = Depends(get_current_user)
):
    try:
        checkpointer = await get_checkpointer()

        thread_id = f"user_{current_user.firebase_uid}"

        checkpoint = await checkpointer.aget({
            "configurable": {
                "thread_id": thread_id
            }
        })

        if not checkpoint:
            return {"messages": []}

        messages = []

        channel_values = checkpoint.get("channel_values", {})
        stored_messages = channel_values.get("messages", [])

        for msg in stored_messages:
            role = "assistant"

            if msg.type == "human":
                role = "user"

            messages.append({
                "role": role,
                "content": msg.content
            })

        return {
            "messages": messages
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))