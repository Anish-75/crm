import logging
from typing import Optional
import jwt
from supabase import Client
from supabase_auth.errors import AuthApiError

from app.config import get_settings
from app.core.exceptions import UnauthorizedError
from app.repositories.profile_repo import ProfileRepository
from app.schemas.auth import CurrentUser, UserRole

logger = logging.getLogger(__name__)


class AuthService:
    """Service for validating Supabase JWTs and loading user roles and profiles."""

    def __init__(self, profile_repo: Optional[ProfileRepository] = None):
        self.profile_repo = profile_repo or ProfileRepository()

    def verify_token(self, token: str, client: Optional[Client] = None) -> CurrentUser:
        """
        Verify the Supabase JWT access token and load the user's role from the `profiles` table.
        - If SUPABASE_JWT_SECRET is configured, validates JWT signature locally via PyJWT.
        - Otherwise, validates via Supabase Auth API (`client.auth.get_user(token)`).
        """
        settings = get_settings()
        user_id: Optional[str] = None
        user_email: Optional[str] = None

        # 1. Local JWT verification if secret is provided
        if settings.SUPABASE_JWT_SECRET:
            try:
                payload = jwt.decode(
                    token,
                    settings.SUPABASE_JWT_SECRET,
                    algorithms=["HS256"],
                    options={"verify_aud": False},  # Supabase tokens use 'authenticated' audience
                )
                user_id = payload.get("sub")
                user_email = payload.get("email")
            except jwt.PyJWTError as e:
                logger.warning(f"JWT signature verification failed: {type(e).__name__}")
                raise UnauthorizedError("Invalid or expired authentication token")

        # 2. Remote Supabase Auth API verification if no secret or fallback
        if not user_id:
            supabase_client = client or self.profile_repo.client
            try:
                user_resp = supabase_client.auth.get_user(token)
                if not user_resp or not user_resp.user:
                    raise UnauthorizedError("Invalid authentication token")
                user_id = user_resp.user.id
                user_email = user_resp.user.email
            except AuthApiError as e:
                logger.warning(f"Supabase Auth validation failed: {e.message}")
                raise UnauthorizedError("Invalid or expired authentication token")
            except Exception as e:
                logger.error(f"Unexpected error validating token with Supabase: {type(e).__name__}")
                raise UnauthorizedError("Authentication failed")

        if not user_id:
            raise UnauthorizedError("Token does not contain a valid user identity")

        # 3. Load user role from `profiles` table (PRD Section 4 & 5)
        profile = self.profile_repo.get_by_id(user_id)
        if profile:
            raw_role = profile.get("role", "agent")
            role = UserRole.ADMIN if raw_role == "admin" else UserRole.AGENT
            full_name = profile.get("full_name")
        else:
            # Fallback for newly created auth user without profile row yet
            role = UserRole.AGENT
            full_name = None

        return CurrentUser(
            id=user_id,
            email=user_email,
            role=role,
            full_name=full_name,
        )

