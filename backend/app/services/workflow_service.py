from typing import Any, Dict, List, Optional
from app.core.exceptions import NotFoundError
from app.repositories.workflow_repo import WorkflowRepository
from app.schemas.workflow import WorkflowCreate, WorkflowUpdate


class WorkflowService:
    """Service handling workflow CRUD."""

    def __init__(self, workflow_repo: Optional[WorkflowRepository] = None):
        self.workflow_repo = workflow_repo or WorkflowRepository()

    def list_workflows(self, active_only: bool = False) -> List[Dict[str, Any]]:
        return self.workflow_repo.list_workflows(active_only=active_only)

    def get_workflow(self, workflow_id: str) -> Dict[str, Any]:
        workflow = self.workflow_repo.get_by_id(workflow_id)
        if not workflow:
            raise NotFoundError(f"Workflow with ID {workflow_id} not found")
        return workflow

    def create_workflow(self, workflow_in: WorkflowCreate) -> Dict[str, Any]:
        return self.workflow_repo.create(workflow_in.model_dump())

    def update_workflow(self, workflow_id: str, workflow_in: WorkflowUpdate) -> Dict[str, Any]:
        self.get_workflow(workflow_id)
        payload = workflow_in.model_dump(exclude_unset=True)
        updated = self.workflow_repo.update(workflow_id, payload)
        if not updated:
            raise NotFoundError(f"Workflow with ID {workflow_id} not found")
        return updated

    def delete_workflow(self, workflow_id: str) -> bool:
        self.get_workflow(workflow_id)
        return self.workflow_repo.delete(workflow_id)

