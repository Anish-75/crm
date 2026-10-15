from typing import Any, Dict, List, Optional
from app.core.exceptions import NotFoundError
from app.repositories.template_repo import TemplateRepository
from app.schemas.template import TemplateCreate, TemplateUpdate


class TemplateService:
    """Service handling email template CRUD."""

    def __init__(self, template_repo: Optional[TemplateRepository] = None):
        self.template_repo = template_repo or TemplateRepository()

    def list_templates(self, active_only: bool = False) -> List[Dict[str, Any]]:
        return self.template_repo.list_templates(active_only=active_only)

    def get_template(self, template_id: str) -> Dict[str, Any]:
        template = self.template_repo.get_by_id(template_id)
        if not template:
            raise NotFoundError(f"Email template with ID {template_id} not found")
        return template

    def create_template(self, template_in: TemplateCreate) -> Dict[str, Any]:
        return self.template_repo.create(template_in.model_dump())

    def update_template(self, template_id: str, template_in: TemplateUpdate) -> Dict[str, Any]:
        self.get_template(template_id)
        payload = template_in.model_dump(exclude_unset=True)
        updated = self.template_repo.update(template_id, payload)
        if not updated:
            raise NotFoundError(f"Email template with ID {template_id} not found")
        return updated

    def delete_template(self, template_id: str) -> bool:
        self.get_template(template_id)
        return self.template_repo.delete(template_id)

