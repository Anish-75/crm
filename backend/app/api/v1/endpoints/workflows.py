from typing import List
from fastapi import APIRouter, Depends, status
from app.core.dependencies import get_current_user, require_admin
from app.schemas.auth import CurrentUser
from app.schemas.common import SuccessResponse
from app.schemas.workflow import (
    WorkflowCreate,
    WorkflowResponse,
    WorkflowUpdate,
)
from app.services.workflow_service import WorkflowService

router = APIRouter(prefix="/workflows", tags=["Workflows"])


def get_workflow_service() -> WorkflowService:
    return WorkflowService()


@router.get("", response_model=List[WorkflowResponse], summary="List workflows")
async def list_workflows(
    current_user: CurrentUser = Depends(get_current_user),
    service: WorkflowService = Depends(get_workflow_service),
) -> List[WorkflowResponse]:
    """Staff can list all workflows."""
    workflows = service.list_workflows()
    return [WorkflowResponse.model_validate(w) for w in workflows]


@router.get("/{id}", response_model=WorkflowResponse, summary="Get workflow by ID")
async def get_workflow(
    id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowResponse:
    workflow = service.get_workflow(id)
    return WorkflowResponse.model_validate(workflow)


@router.post(
    "",
    response_model=WorkflowResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create workflow (Admin only)",
)
async def create_workflow(
    workflow_in: WorkflowCreate,
    admin_user: CurrentUser = Depends(require_admin),
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowResponse:
    created = service.create_workflow(workflow_in)
    return WorkflowResponse.model_validate(created)


@router.patch("/{id}", response_model=WorkflowResponse, summary="Update workflow (Admin only)")
async def update_workflow(
    id: str,
    workflow_in: WorkflowUpdate,
    admin_user: CurrentUser = Depends(require_admin),
    service: WorkflowService = Depends(get_workflow_service),
) -> WorkflowResponse:
    updated = service.update_workflow(id, workflow_in)
    return WorkflowResponse.model_validate(updated)


@router.delete("/{id}", response_model=SuccessResponse, summary="Delete workflow (Admin only)")
async def delete_workflow(
    id: str,
    admin_user: CurrentUser = Depends(require_admin),
    service: WorkflowService = Depends(get_workflow_service),
) -> SuccessResponse:
    service.delete_workflow(id)
    return SuccessResponse(success=True, message=f"Workflow {id} deleted successfully")

