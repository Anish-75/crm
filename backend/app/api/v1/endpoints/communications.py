import math
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from app.core.dependencies import get_current_user
from app.schemas.auth import CurrentUser
from app.schemas.common import PaginatedResponse
from app.schemas.communication import (
    CommunicationResponse,
    CommunicationSendRequest,
)
from app.services.communication_service import CommunicationService

router = APIRouter(prefix="/communications", tags=["Communications"])


def get_communication_service() -> CommunicationService:
    return CommunicationService()


@router.get("", response_model=PaginatedResponse[CommunicationResponse], summary="List communications")
async def list_communications(
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
    order_id: Optional[str] = Query(None, description="Filter by order ID"),
    status: Optional[str] = Query(None, description="Filter by status (queued, sent, failed)"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: CurrentUser = Depends(get_current_user),
    service: CommunicationService = Depends(get_communication_service),
) -> PaginatedResponse[CommunicationResponse]:
    items, total = service.list_communications(
        customer_id=customer_id,
        order_id=order_id,
        status=status,
        page=page,
        per_page=per_page,
    )
    total_pages = math.ceil(total / per_page) if total > 0 else 0
    return PaginatedResponse(
        items=[CommunicationResponse.model_validate(c) for c in items],
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
    )


@router.post(
    "/send",
    response_model=CommunicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send communication to a customer",
)
async def send_communication(
    req: CommunicationSendRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: CommunicationService = Depends(get_communication_service),
) -> CommunicationResponse:
    result = service.send_communication(req)
    return CommunicationResponse.model_validate(result)

