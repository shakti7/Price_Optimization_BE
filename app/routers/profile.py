from fastapi import APIRouter, Depends
from app.models.user import User
from app.schemas.user import UserResponse
from app.core.auth_guard import get_current_user

router = APIRouter(
    prefix="/profile",
    tags=["User Profile"]
)

@router.get("/", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    """Returns the authenticated user's profile."""
    return current_user
