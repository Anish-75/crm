from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_user
from app.schemas.auth import CurrentUser

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.get("/me", response_model=CurrentUser, summary="Get current authenticated user and profile")
async def get_me(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Return the profile and role of the currently authenticated Supabase user."""
    return current_user

