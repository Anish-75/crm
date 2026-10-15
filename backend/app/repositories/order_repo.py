from typing import Any, Dict, List, Optional, Tuple
from app.repositories.base import BaseRepository


class OrderRepository(BaseRepository):
    """Repository for interacting with `orders`, `order_items`, and `order_status_history` tables."""

    def list_orders(
        self,
        status: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """List orders with filters and pagination."""
        query = self.client.table("orders").select("*, customers(*)", count="exact")

        if status:
            query = query.eq("status", status)

        if date_from:
            query = query.gte("placed_at", date_from)

        if date_to:
            query = query.lte("placed_at", date_to)

        if search:
            if search.isdigit():
                query = query.eq("woo_order_id", int(search))

        query = query.order("placed_at", desc=True)

        start = (page - 1) * per_page
        end = start + per_page - 1
        query = query.range(start, end)

        response = query.execute()
        return response.data or [], response.count or 0

    def get_by_id(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get order by UUID including customer and items."""
        response = (
            self.client.table("orders")
            .select("*, customers(*), order_items(*)")
            .eq("id", order_id)
            .maybe_single()
            .execute()
        )
        return response.data

    def get_by_woo_id(self, woo_order_id: int) -> Optional[Dict[str, Any]]:
        """Get order by WooCommerce order ID."""
        response = (
            self.client.table("orders")
            .select("*")
            .eq("woo_order_id", woo_order_id)
            .maybe_single()
            .execute()
        )
        return response.data

    def update_status(
        self,
        order_id: str,
        to_status: str,
        source: str = "crm",
        from_status: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Update an order's status and record in `order_status_history`."""
        # 1. Update order
        response = (
            self.client.table("orders")
            .update({"status": to_status})
            .eq("id", order_id)
            .execute()
        )
        if not response.data:
            return None

        # 2. Record history
        history_record = {
            "order_id": order_id,
            "from_status": from_status,
            "to_status": to_status,
            "source": source,
        }
        self.client.table("order_status_history").insert(history_record).execute()

        return response.data[0]

    def get_items(self, order_id: str) -> List[Dict[str, Any]]:
        """Fetch items belonging to an order."""
        response = (
            self.client.table("order_items")
            .select("*")
            .eq("order_id", order_id)
            .execute()
        )
        return response.data or []

    def get_history(self, order_id: str) -> List[Dict[str, Any]]:
        """Fetch status history for an order."""
        response = (
            self.client.table("order_status_history")
            .select("*")
            .eq("order_id", order_id)
            .order("changed_at", desc=True)
            .execute()
        )
        return response.data or []

