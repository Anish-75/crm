from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class TemplateBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    trigger_event: str = Field(
        ...,
        description="Trigger event name, e.g. order.created, order.status_changed, customer.created",
    )
    subject: str = Field(..., min_length=1, max_length=500)
    body_html: str = Field(..., min_length=1, description="HTML body with {{variables}}")
    is_active: bool = True


class TemplateCreate(TemplateBase):
    pass


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    trigger_event: Optional[str] = None
    subject: Optional[str] = None
    body_html: Optional[str] = None
    is_active: Optional[bool] = None


class TemplateResponse(TemplateBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

