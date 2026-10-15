from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class UserRole(str, Enum):
    ADMIN = "admin"
    AGENT = "agent"


class UserProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="User UUID corresponding to auth.users.id")
    full_name: Optional[str] = None
    role: UserRole = UserRole.AGENT
    created_at: Optional[datetime] = None


class CurrentUser(BaseModel):
    id: str = Field(..., description="User UUID")
    email: Optional[str] = None
    role: UserRole = UserRole.AGENT
    full_name: Optional[str] = None

    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN

    @property
    def is_agent(self) -> bool:
        return self.role == UserRole.AGENT

