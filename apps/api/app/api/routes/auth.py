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