from app.core.dependencies import (
    get_auth_service,
    get_current_user,
    get_db_client,
    oauth2_scheme,
    require_admin,
    require_staff,
)
from app.core.exceptions import (
    ConflictError,
    CRMException,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
    register_exception_handlers,
)

__all__ = [
    "get_auth_service",
    "get_current_user",
    "get_db_client",
    "oauth2_scheme",
    "require_admin",
    "require_staff",
    "CRMException",
    "UnauthorizedError",
    "ForbiddenError",
    "NotFoundError",
    "ConflictError",
    "ValidationError",
    "register_exception_handlers",
]
