from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.services.agents.first_agent import run_first_agent
from app.dependencies.auth import get_current_user
from app.db.models.user import User

router = APIRouter(prefix="/agent", tags=["Agent"])

class AgentRequest(BaseModel):
    query: str

class AgentResponse(BaseModel):
    response: str
    thread_id: str
    success: bool = True


# Endpoint principal (com autenticação)
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


# ==================== ENDPOINT DE TESTE (SEM AUTH) ====================
@router.post("/chat-test", response_model=AgentResponse)
async def chat_with_agent_test(request: AgentRequest):
    """Endpoint temporário para testes sem precisar de token Firebase"""
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