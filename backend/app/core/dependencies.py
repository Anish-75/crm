from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import Client

from app.core.exceptions import UnauthorizedError
from app.db.supabase import get_supabase_client
from app.repositories.profile_repo import ProfileRepository
from app.schemas.auth import CurrentUser, UserRole
from app.services.auth_service import AuthService

# Bearer security scheme for OpenAPI documentation and header extraction
oauth2_scheme = HTTPBearer(
    auto_error=False,
    description="Supabase Auth JWT Bearer Token",
)


def get_db_client() -> Client:
    """Dependency that returns the server-side Supabase client with service role key."""
    return get_supabase_client()


def get_auth_service(client: Client = Depends(get_db_client)) -> AuthService:
    """Dependency that provides the AuthService instance."""
    profile_repo = ProfileRepository(client=client)
    return AuthService(profile_repo=profile_repo)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
    client: Client = Depends(get_db_client),
) -> CurrentUser:
    """
    Dependency to authenticate requests with a valid Supabase JWT and load user role from `profiles`.
    Raises HTTP 401 if token is missing, invalid, or expired.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        current_user = auth_service.verify_token(token, client=client)
        return current_user
    except UnauthorizedError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=exc.message,
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_admin(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """
    Dependency that ensures the authenticated user has the 'admin' role.
    Raises HTTP 403 Forbidden if the user is an agent or other role.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


def require_staff(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """
    Dependency that ensures the user is a staff member (agent or admin).
    """
    if current_user.role not in (UserRole.ADMIN, UserRole.AGENT):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff privileges required",
        )
    return current_user

