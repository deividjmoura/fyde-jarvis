from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.services.agents.first_agent import run_first_agent
from app.dependencies.auth import get_current_user  # Vamos criar isso
from app.db.models.user import User

router = APIRouter(prefix="/agent", tags=["Agent"])

class AgentRequest(BaseModel):
    query: str
    # thread_id agora é opcional (vamos gerar por usuário)

class AgentResponse(BaseModel):
    response: str
    thread_id: str
    success: bool = True

@router.post("/chat", response_model=AgentResponse)
async def chat_with_agent(
    request: AgentRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        # Cria thread_id único por usuário (pode ter várias conversas no futuro)
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