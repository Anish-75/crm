from typing import Any, Dict, List, Optional
from app.repositories.base import BaseRepository


class WorkflowRepository(BaseRepository):
    """Repository for managing communication workflows in Supabase."""

    def list_workflows(self, active_only: bool = False) -> List[Dict[str, Any]]:
        """List all workflows."""
        query = self.client.table("workflows").select("*, email_templates(*)")
        if active_only:
            query = query.eq("is_active", True)
        response = query.order("name").execute()
        return response.data or []

    def get_by_id(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow by UUID."""
        response = (
            self.client.table("workflows")
            .select("*, email_templates(*)")
            .eq("id", workflow_id)
            .maybe_single()
            .execute()
        )
        return response.data

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new workflow."""
        response = self.client.table("workflows").insert(data).execute()
        return response.data[0]

    def update(self, workflow_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing workflow."""
        response = (
            self.client.table("workflows")
            .update(data)
            .eq("id", workflow_id)
            .execute()
        )
        return response.data[0] if response.data else None

    def delete(self, workflow_id: str) -> bool:
        """Delete a workflow by UUID."""
        response = (
            self.client.table("workflows")
            .delete()
            .eq("id", workflow_id)
            .execute()
        )
        return bool(response.data)

