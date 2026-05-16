from fastapi import APIRouter, Depends

from app.dependencies.auth import get_current_user


router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)


@router.get("/me")
def get_me(
    current_user = Depends(get_current_user)
):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "firebase_uid": current_user.firebase_uid
    }
# ==================== TESTE TEMPORÁRIO ====================
@router.get("/test-token")
def get_test_token():
    """Endpoint temporário para pegar um usuário de teste"""
    return {
        "message": "Use este token para testar (válido por enquanto)",
        "test_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmaXJlYmFzZV91aWQiOiJ0ZXN0X3VzZXJfMTIzIiwicm9sZSI6InRlc3QifQ.test",
        "instructions": "Cole este token no Authorization: Bearer <token>"
    }