from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class SyncType(str, Enum):
    WEBHOOK = "webhook"
    FULL = "full"
    INCREMENTAL = "incremental"


class SyncStatus(str, Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


class SyncTriggerRequest(BaseModel):
    type: SyncType = SyncType.FULL


class SyncLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: SyncType
    resource: str
    status: SyncStatus
    details: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class SyncStatusResponse(BaseModel):
    is_syncing: bool = False
    last_sync: Optional[SyncLogResponse] = None
    recent_logs: List[SyncLogResponse] = Field(default_factory=list)

