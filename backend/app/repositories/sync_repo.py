from typing import Any, Dict, List, Optional
from app.repositories.base import BaseRepository


class SyncRepository(BaseRepository):
    """Repository for managing sync logs and webhook event deduplication."""

    def create_log(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a sync_logs row."""
        response = self.client.table("sync_logs").insert(data).execute()
        return response.data[0]

    def get_recent_logs(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Fetch the most recent sync logs."""
        response = (
            self.client.table("sync_logs")
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        if response.data and isinstance(response.data, list):
            return [item for item in response.data if isinstance(item, dict)]
        return []

    def get_latest_sync(self) -> Optional[Dict[str, Any]]:
        """Fetch the latest sync record."""
        response = (
            self.client.table("sync_logs")
            .select("*")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        if (
            response.data
            and isinstance(response.data, list)
            and len(response.data) > 0
            and isinstance(response.data[0], dict)
        ):
            return response.data[0]
        return None

    def record_webhook_event(
        self,
        woo_delivery_id: str,
        topic: str,
        payload: Dict[str, Any],
        processed: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """Record a webhook event for deduplication."""
        data = {
            "woo_delivery_id": woo_delivery_id,
            "topic": topic,
            "payload": payload,
            "processed": processed,
        }
        response = self.client.table("webhook_events").insert(data).execute()
        return response.data[0] if response.data else None

    def get_webhook_event(self, woo_delivery_id: str) -> Optional[Dict[str, Any]]:
        """Check if a webhook event with the given delivery ID has already been received."""
        response = (
            self.client.table("webhook_events")
            .select("*")
            .eq("woo_delivery_id", woo_delivery_id)
            .maybe_single()
            .execute()
        )
        return response.data
