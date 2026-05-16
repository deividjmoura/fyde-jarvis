from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.agents.first_agent import run_first_agent

router = APIRouter(prefix="/agent", tags=["Agent"])

class AgentRequest(BaseModel):
    query: str
    thread_id: str = "default"

class AgentResponse(BaseModel):
    response: str
    success: bool = True

@router.post("/chat", response_model=AgentResponse)
async def chat_with_agent(request: AgentRequest):
    try:
        response_text = await run_first_agent(
            query=request.query,
            thread_id=request.thread_id
        )
        
        return AgentResponse(response=response_text, success=True)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
