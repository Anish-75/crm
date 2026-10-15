from typing import Any, Dict, List, Optional
from app.repositories.base import BaseRepository


class TemplateRepository(BaseRepository):
    """Repository for managing email templates in Supabase."""

    def list_templates(self, active_only: bool = False) -> List[Dict[str, Any]]:
        """List all templates."""
        query = self.client.table("email_templates").select("*")
        if active_only:
            query = query.eq("is_active", True)
        response = query.order("name").execute()
        return response.data or []

    def get_by_id(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get template by UUID."""
        response = (
            self.client.table("email_templates")
            .select("*")
            .eq("id", template_id)
            .maybe_single()
            .execute()
        )
        return response.data

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new template."""
        response = self.client.table("email_templates").insert(data).execute()
        return response.data[0]

    def update(self, template_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing template."""
        response = (
            self.client.table("email_templates")
            .update(data)
            .eq("id", template_id)
            .execute()
        )
        return response.data[0] if response.data else None

    def delete(self, template_id: str) -> bool:
        """Delete a template by UUID."""
        response = (
            self.client.table("email_templates")
            .delete()
            .eq("id", template_id)
            .execute()
        )
        return bool(response.data)

