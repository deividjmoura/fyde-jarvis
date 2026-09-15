from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services.agents.first_agent import run_first_agent
from app.services.agents.streaming import astream_agent_tokens, sse_pack
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


# ==================== CHAT STREAMING AUTENTICADO (SSE) ====================
@router.post("/chat-stream")
async def chat_with_agent_stream(
    request: AgentRequest,
    current_user: User = Depends(get_current_user),
):
    """Versão SSE do `/agent/chat` (Firebase auth): resposta em tempo real.

    Diferencia do `/agent/chat-test-stream` em dois pontos:
      - exige Firebase ID Token (Bearer);
      - o `thread_id` é isolado por usuário (`user_<firebase_uid>`), igual ao
        `/agent/chat`, então a memória nunca se mistura entre usuários.

    Contrato de eventos é o mesmo do endpoint de teste (um por linha `data: `):
      {"type": "token", "content": "..."}
      {"type": "done"}
      {"type": "error", "detail": "..."}
    """

    async def event_stream():
        thread_id = f"user_{current_user.firebase_uid}"
        try:
            async for token in astream_agent_tokens(request.query, thread_id):
                yield sse_pack({"type": "token", "content": token})
            yield sse_pack({"type": "done"})
        except Exception as e:
            yield sse_pack({"type": "error", "detail": str(e)})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # desativa buffer em proxies (nginx)
        },
    )


# ==================== CHAT TESTE STREAMING (SSE) ====================
@router.post("/chat-test-stream")
async def chat_with_agent_test_stream(request: AgentRequest):
    """Versão SSE do /chat-test: emite a resposta em tempo real.

    Formato dos eventos (um por linha, prefixo `data: `):
      {"type": "token", "content": "..."}   → pedaço de texto da resposta
      {"type": "done"}                       → resposta finalizada
      {"type": "error", "detail": "..."}     → falha no meio do caminho
    """

    async def event_stream():
        thread_id = "test_user_123"
        try:
            async for token in astream_agent_tokens(request.query, thread_id):
                yield sse_pack({"type": "token", "content": token})
            yield sse_pack({"type": "done"})
        except Exception as e:
            yield sse_pack({"type": "error", "detail": str(e)})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # desativa buffer em proxies (nginx)
        },
    )


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