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

    def upsert_from_woo(
        self,
        woo_order_data: Dict[str, Any],
        customer_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Upsert order from WooCommerce data.
        Conforms strictly to DATABASE.md section 9:
        1. insert ... on conflict (woo_order_id) do update set ...
        2. For items, delete and reinsert.
        3. Record a status change only when it differs: compare orders.status
           to incoming status before inserting into order_status_history.
        4. Refresh customer totals after an order upsert.
        """
        from app.repositories.customer_repo import CustomerRepository
        from app.services.woo_mapper import (
            map_woo_order_items_to_db,
            map_woo_order_to_db,
        )

        customer_repo = CustomerRepository(client=self.client)

        # 1. Resolve customer if not explicitly provided
        if not customer_id:
            raw_cust_id = woo_order_data.get("customer_id")
            woo_cust_id = int(raw_cust_id) if raw_cust_id is not None and int(raw_cust_id) > 0 else None
            billing_email = (woo_order_data.get("billing") or {}).get("email")

            if woo_cust_id:
                cust = customer_repo.get_by_woo_id(woo_cust_id)
                if cust:
                    customer_id = cust["id"]

            if not customer_id and billing_email:
                # Match or create guest customer by billing email (PRD Section 6)
                cust = customer_repo.get_by_email(billing_email)
                if not cust:
                    cust = customer_repo.upsert_from_woo(
                        {
                            "id": 0,
                            "email": billing_email,
                            "first_name": (woo_order_data.get("billing") or {}).get("first_name", ""),
                            "last_name": (woo_order_data.get("billing") or {}).get("last_name", ""),
                            "phone": (woo_order_data.get("billing") or {}).get("phone"),
                            "billing": woo_order_data.get("billing") or {},
                            "shipping": woo_order_data.get("shipping") or {},
                        }
                    )
                if cust:
                    customer_id = cust["id"]

        woo_order_id = int(woo_order_data["id"])
        existing_order = self.get_by_woo_id(woo_order_id)
        previous_status = existing_order.get("status") if existing_order else None
        new_status = str(woo_order_data.get("status", "pending")).lower()

        mapped_order = map_woo_order_to_db(woo_order_data, customer_id=customer_id)

        # 2. Upsert order row
        if existing_order:
            order_id = existing_order["id"]
            resp = (
                self.client.table("orders")
                .update(mapped_order)
                .eq("id", order_id)
                .execute()
            )
            saved_order = resp.data[0] if resp.data else {**existing_order, **mapped_order}
        else:
            resp = self.client.table("orders").insert(mapped_order).execute()
            saved_order = resp.data[0] if resp.data else mapped_order
            order_id = saved_order.get("id")

        # 3. For items: delete and reinsert (DATABASE.md section 9)
        if order_id:
            self.client.table("order_items").delete().eq("order_id", order_id).execute()
            raw_items = woo_order_data.get("line_items") or []
            mapped_items = map_woo_order_items_to_db(raw_items, order_id=order_id)
            if mapped_items:
                self.client.table("order_items").insert(mapped_items).execute()
            saved_order["order_items"] = mapped_items

        # 4. Record status change only when it differs (DATABASE.md section 9)
        if order_id and previous_status != new_status:
            history_record = {
                "order_id": order_id,
                "from_status": previous_status,
                "to_status": new_status,
                "source": "woo",
            }
            self.client.table("order_status_history").insert(history_record).execute()

        # 5. Refresh customer totals after order upsert (DATABASE.md section 9)
        if customer_id:
            customer_repo.refresh_customer_totals(customer_id)

        return saved_order

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

