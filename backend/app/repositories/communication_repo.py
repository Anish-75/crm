from typing import Any, Dict, List, Optional, Tuple
from app.repositories.base import BaseRepository


class CommunicationRepository(BaseRepository):
    """Repository for managing logged communications in Supabase."""

    def list_communications(
        self,
        customer_id: Optional[str] = None,
        order_id: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """List communications with filters and pagination."""
        query = self.client.table("communications").select("*", count="exact")

        if customer_id:
            query = query.eq("customer_id", customer_id)
        if order_id:
            query = query.eq("order_id", order_id)
        if status:
            query = query.eq("status", status)

        query = query.order("created_at", desc=True)

        start = (page - 1) * per_page
        end = start + per_page - 1
        query = query.range(start, end)

        response = query.execute()
        return response.data or [], response.count or 0

    def get_by_id(self, communication_id: str) -> Optional[Dict[str, Any]]:
        """Get communication by UUID."""
        response = (
            self.client.table("communications")
            .select("*")
            .eq("id", communication_id)
            .maybe_single()
            .execute()
        )
        return response.data

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a communication record."""
        response = self.client.table("communications").insert(data).execute()
        return response.data[0]

    def update_status(
        self,
        communication_id: str,
        status: str,
        error: Optional[str] = None,
        sent_at: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Update communication status (queued -> sent or failed)."""
        data: Dict[str, Any] = {"status": status}
        if error is not None:
            data["error"] = error
        if sent_at is not None:
            data["sent_at"] = sent_at

        response = (
            self.client.table("communications")
            .update(data)
            .eq("id", communication_id)
            .execute()
        )
        return response.data[0] if response.data else None

