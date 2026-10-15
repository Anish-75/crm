from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CustomerBase(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    billing: Dict[str, Any] = Field(default_factory=dict)
    shipping: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)


class CustomerCreate(CustomerBase):
    woo_customer_id: Optional[int] = None


class CustomerUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    billing: Optional[Dict[str, Any]] = None
    shipping: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class CustomerResponse(CustomerBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    woo_customer_id: Optional[int] = None
    total_spent: Decimal = Decimal("0.00")
    orders_count: int = 0
    created_at: datetime
    updated_at: datetime
    synced_at: Optional[datetime] = None


class CustomerNoteCreate(BaseModel):
    body: str = Field(..., min_length=1, max_length=5000, description="Note content")


class CustomerNoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    customer_id: str
    author_id: str
    body: str
    created_at: datetime

