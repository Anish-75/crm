import math
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from app.core.dependencies import get_current_user
from app.schemas.auth import CurrentUser
from app.schemas.common import PaginatedResponse
from app.schemas.order import (
    OrderItemResponse,
    OrderResponse,
    OrderStatusHistoryResponse,
    OrderStatusUpdate,
)
from app.services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["Orders"])


def get_order_service() -> OrderService:
    return OrderService()


@router.get("", response_model=PaginatedResponse[OrderResponse], summary="List orders")
async def list_orders(
    status: Optional[str] = Query(None, description="Filter by order status"),
    date_from: Optional[str] = Query(None, description="Start date ISO string"),
    date_to: Optional[str] = Query(None, description="End date ISO string"),
    search: Optional[str] = Query(None, description="Search by order ID"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: CurrentUser = Depends(get_current_user),
    service: OrderService = Depends(get_order_service),
) -> PaginatedResponse[OrderResponse]:
    items, total = service.list_orders(
        status=status,
        date_from=date_from,
        date_to=date_to,
        search=search,
        page=page,
        per_page=per_page,
    )
    total_pages = math.ceil(total / per_page) if total > 0 else 0
    return PaginatedResponse(
        items=[OrderResponse.model_validate(o) for o in items],
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
    )


@router.get("/{id}", response_model=OrderResponse, summary="Get order by ID")
async def get_order(
    id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: OrderService = Depends(get_order_service),
) -> OrderResponse:
    order = service.get_order(id)
    return OrderResponse.model_validate(order)


@router.patch("/{id}/status", response_model=OrderResponse, summary="Update order status")
async def update_order_status(
    id: str,
    status_update: OrderStatusUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    service: OrderService = Depends(get_order_service),
) -> OrderResponse:
    updated = service.update_order_status(
        order_id=id,
        status_update=status_update,
        source="crm",
    )
    return OrderResponse.model_validate(updated)


@router.get("/{id}/items", response_model=List[OrderItemResponse], summary="Get items in order")
async def get_order_items(
    id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: OrderService = Depends(get_order_service),
) -> List[OrderItemResponse]:
    items = service.get_order_items(id)
    return [OrderItemResponse.model_validate(item) for item in items]


@router.get(
    "/{id}/history",
    response_model=List[OrderStatusHistoryResponse],
    summary="Get status change history of order",
)
async def get_order_history(
    id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: OrderService = Depends(get_order_service),
) -> List[OrderStatusHistoryResponse]:
    history = service.get_order_history(id)
    return [OrderStatusHistoryResponse.model_validate(h) for h in history]

