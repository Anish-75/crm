from typing import List
from fastapi import APIRouter, Depends, status
from app.core.dependencies import get_current_user, require_admin
from app.schemas.auth import CurrentUser
from app.schemas.common import SuccessResponse
from app.schemas.template import (
    TemplateCreate,
    TemplateResponse,
    TemplateUpdate,
)
from app.services.template_service import TemplateService

router = APIRouter(prefix="/templates", tags=["Templates"])


def get_template_service() -> TemplateService:
    return TemplateService()


@router.get("", response_model=List[TemplateResponse], summary="List email templates")
async def list_templates(
    current_user: CurrentUser = Depends(get_current_user),
    service: TemplateService = Depends(get_template_service),
) -> List[TemplateResponse]:
    """Staff can list all email templates."""
    templates = service.list_templates()
    return [TemplateResponse.model_validate(t) for t in templates]


@router.get("/{id}", response_model=TemplateResponse, summary="Get email template by ID")
async def get_template(
    id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: TemplateService = Depends(get_template_service),
) -> TemplateResponse:
    template = service.get_template(id)
    return TemplateResponse.model_validate(template)


@router.post(
    "",
    response_model=TemplateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create email template (Admin only)",
)
async def create_template(
    template_in: TemplateCreate,
    admin_user: CurrentUser = Depends(require_admin),
    service: TemplateService = Depends(get_template_service),
) -> TemplateResponse:
    created = service.create_template(template_in)
    return TemplateResponse.model_validate(created)


@router.patch("/{id}", response_model=TemplateResponse, summary="Update email template (Admin only)")
async def update_template(
    id: str,
    template_in: TemplateUpdate,
    admin_user: CurrentUser = Depends(require_admin),
    service: TemplateService = Depends(get_template_service),
) -> TemplateResponse:
    updated = service.update_template(id, template_in)
    return TemplateResponse.model_validate(updated)


@router.delete("/{id}", response_model=SuccessResponse, summary="Delete email template (Admin only)")
async def delete_template(
    id: str,
    admin_user: CurrentUser = Depends(require_admin),
    service: TemplateService = Depends(get_template_service),
) -> SuccessResponse:
    service.delete_template(id)
    return SuccessResponse(success=True, message=f"Template {id} deleted successfully")

