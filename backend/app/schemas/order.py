from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.customer import CustomerResponse


class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    order_id: str
    woo_product_id: Optional[int] = None
    name: str
    sku: Optional[str] = None
    quantity: int
    price: Decimal
    total: Decimal


class OrderStatusHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    order_id: str
    from_status: Optional[str] = None
    to_status: str
    source: str = "crm"
    changed_at: datetime


class OrderStatusUpdate(BaseModel):
    status: str = Field(..., description="WooCommerce status, e.g. completed, processing, cancelled")


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    woo_order_id: int
    customer_id: Optional[str] = None
    status: str
    currency: str = "USD"
    total: Decimal = Decimal("0.00")
    payment_method: Optional[str] = None
    billing: Dict[str, Any] = Field(default_factory=dict)
    shipping: Dict[str, Any] = Field(default_factory=dict)
    placed_at: datetime
    created_at: datetime
    updated_at: datetime
    synced_at: Optional[datetime] = None
    items: Optional[List[OrderItemResponse]] = None
    customer: Optional[CustomerResponse] = None

