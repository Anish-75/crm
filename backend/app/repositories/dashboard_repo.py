from typing import Any, Dict, List
from app.repositories.base import BaseRepository


class DashboardRepository(BaseRepository):
    """Repository for querying aggregated dashboard metrics."""

    def get_stats(self) -> Dict[str, Any]:
        """Aggregate metrics for the dashboard view."""
        # 1. Orders count & status breakdown
        orders_resp = self.client.table("orders").select("id, total, status, placed_at").execute()
        orders = orders_resp.data or []

        total_revenue = sum(float(o.get("total") or 0) for o in orders)
        order_count = len(orders)

        orders_by_status: Dict[str, int] = {}
        for o in orders:
            status = o.get("status", "unknown")
            orders_by_status[status] = orders_by_status.get(status, 0) + 1

        # 2. Customers
        customers_resp = (
            self.client.table("customers")
            .select("id, first_name, last_name, email, total_spent, orders_count, created_at")
            .order("total_spent", desc=True)
            .execute()
        )
        customers = customers_resp.data or []
        customer_count = len(customers)

        top_customers = customers[:5]

        return {
            "total_revenue": total_revenue,
            "order_count": order_count,
            "customer_count": customer_count,
            "orders_by_status": orders_by_status,
            "top_customers": top_customers,
        }

