import math
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from app.core.dependencies import get_current_user
from app.schemas.auth import CurrentUser
from app.schemas.common import PaginatedResponse
from app.schemas.communication import CommunicationResponse
from app.schemas.customer import (
    CustomerNoteCreate,
    CustomerNoteResponse,
    CustomerResponse,
    CustomerUpdate,
)
from app.schemas.order import OrderResponse
from app.services.customer_service import CustomerService

router = APIRouter(prefix="/customers", tags=["Customers"])


def get_customer_service() -> CustomerService:
    return CustomerService()


@router.get("", response_model=PaginatedResponse[CustomerResponse], summary="List customers")
async def list_customers(
    search: Optional[str] = Query(None, description="Search by name or email"),
    tag: Optional[str] = Query(None, description="Filter by customer tag"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    current_user: CurrentUser = Depends(get_current_user),
    service: CustomerService = Depends(get_customer_service),
) -> PaginatedResponse[CustomerResponse]:
    items, total = service.list_customers(
        search=search,
        tag=tag,
        page=page,
        per_page=per_page,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    total_pages = math.ceil(total / per_page) if total > 0 else 0
    return PaginatedResponse(
        items=[CustomerResponse.model_validate(c) for c in items],
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
    )


@router.get("/{id}", response_model=CustomerResponse, summary="Get customer by ID")
async def get_customer(
    id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: CustomerService = Depends(get_customer_service),
) -> CustomerResponse:
    customer = service.get_customer(id)
    return CustomerResponse.model_validate(customer)


@router.patch("/{id}", response_model=CustomerResponse, summary="Update customer details")
async def update_customer(
    id: str,
    update_data: CustomerUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    service: CustomerService = Depends(get_customer_service),
) -> CustomerResponse:
    customer = service.update_customer(id, update_data)
    return CustomerResponse.model_validate(customer)


@router.post(
    "/{id}/notes",
    response_model=CustomerNoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a note to customer",
)
async def add_customer_note(
    id: str,
    note_in: CustomerNoteCreate,
    current_user: CurrentUser = Depends(get_current_user),
    service: CustomerService = Depends(get_customer_service),
) -> CustomerNoteResponse:
    note = service.add_note(customer_id=id, author_id=current_user.id, note_data=note_in)
    return CustomerNoteResponse.model_validate(note)


@router.get("/{id}/notes", response_model=List[CustomerNoteResponse], summary="Get customer notes")
async def get_customer_notes(
    id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: CustomerService = Depends(get_customer_service),
) -> List[CustomerNoteResponse]:
    notes = service.get_notes(id)
    return [CustomerNoteResponse.model_validate(n) for n in notes]


@router.get("/{id}/orders", response_model=List[OrderResponse], summary="Get customer orders")
async def get_customer_orders(
    id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: CustomerService = Depends(get_customer_service),
) -> List[OrderResponse]:
    orders = service.get_orders(id)
    return [OrderResponse.model_validate(o) for o in orders]


@router.get(
    "/{id}/communications",
    response_model=List[CommunicationResponse],
    summary="Get customer communications",
)
async def get_customer_communications(
    id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: CustomerService = Depends(get_customer_service),
) -> List[CommunicationResponse]:
    comms = service.get_communications(id)
    return [CommunicationResponse.model_validate(c) for c in comms]
