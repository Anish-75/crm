from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class CommChannel(str, Enum):
    EMAIL = "email"


class CommStatus(str, Enum):
    QUEUED = "queued"
    SENT = "sent"
    FAILED = "failed"


class CommunicationSendRequest(BaseModel):
    customer_id: str = Field(..., description="Target customer UUID")
    order_id: Optional[str] = Field(default=None, description="Optional associated order UUID")
    template_id: Optional[str] = Field(default=None, description="Template UUID to render")
    subject: Optional[str] = Field(default=None, description="Custom subject or override")
    body: Optional[str] = Field(default=None, description="Custom body or override")


class CommunicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    customer_id: str
    order_id: Optional[str] = None
    template_id: Optional[str] = None
    channel: CommChannel = CommChannel.EMAIL
    subject: str
    body: str
    status: CommStatus = CommStatus.QUEUED
    error: Optional[str] = None
    sent_at: Optional[datetime] = None
    created_at: datetime

