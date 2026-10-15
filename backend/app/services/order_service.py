from typing import Any, Dict, List, Optional, Tuple
from app.core.exceptions import NotFoundError
from app.repositories.order_repo import OrderRepository
from app.schemas.order import OrderStatusUpdate


class OrderService:
    """Service handling order business logic."""

    def __init__(self, order_repo: Optional[OrderRepository] = None):
        self.order_repo = order_repo or OrderRepository()

    def list_orders(
        self,
        status: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> Tuple[List[Dict[str, Any]], int]:
        return self.order_repo.list_orders(
            status=status,
            date_from=date_from,
            date_to=date_to,
            search=search,
            page=page,
            per_page=per_page,
        )

    def get_order(self, order_id: str) -> Dict[str, Any]:
        order = self.order_repo.get_by_id(order_id)
        if not order:
            raise NotFoundError(f"Order with ID {order_id} not found")
        return order

    async def update_order_status(
        self,
        order_id: str,
        status_update: OrderStatusUpdate,
        source: str = "crm",
    ) -> Dict[str, Any]:
        current_order = self.get_order(order_id)
        from_status = current_order.get("status")
        woo_order_id = current_order.get("woo_order_id")

        # Push to WooCommerce if updated from CRM and WooCommerce is configured
        if source == "crm" and woo_order_id:
            from app.services.woocommerce_client import WooCommerceClient
            woo = WooCommerceClient()
            if woo.base_url and woo.consumer_key:
                try:
                    await woo.update_order_status(woo_order_id, status_update.status)
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).warning(f"Could not push status to WooCommerce: {e}")

        updated = self.order_repo.update_status(
            order_id=order_id,
            to_status=status_update.status,
            source=source,
            from_status=from_status,
        )
        if not updated:
            raise NotFoundError(f"Order with ID {order_id} not found")
        return updated

    def get_order_items(self, order_id: str) -> List[Dict[str, Any]]:
        self.get_order(order_id)
        return self.order_repo.get_items(order_id)

    def get_order_history(self, order_id: str) -> List[Dict[str, Any]]:
        self.get_order(order_id)
        return self.order_repo.get_history(order_id)

