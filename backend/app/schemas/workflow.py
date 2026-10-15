from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field


class WorkflowBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    trigger: str = Field(
        ...,
        description="Trigger name: order.created, order.status_changed, or customer.created",
    )
    conditions: Dict[str, Any] = Field(default_factory=dict, description="e.g. {'to_status': 'completed'}")
    template_id: Optional[str] = None
    delay_minutes: int = Field(default=0, ge=0)
    is_active: bool = True


class WorkflowCreate(WorkflowBase):
    pass


class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    trigger: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None
    template_id: Optional[str] = None
    delay_minutes: Optional[int] = Field(default=None, ge=0)
    is_active: Optional[bool] = None


class WorkflowResponse(WorkflowBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

