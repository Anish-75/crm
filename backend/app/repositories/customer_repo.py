from typing import Any, Dict, List, Optional, Tuple
from app.repositories.base import BaseRepository


class CustomerRepository(BaseRepository):
    """Repository for interacting with the `customers` and `customer_notes` tables in Supabase."""

    def list_customers(
        self,
        search: Optional[str] = None,
        tag: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Tuple[List[Dict[str, Any]], int]:
        """List customers with search, tag filter, pagination, and sorting."""
        query = self.client.table("customers").select("*", count="exact")

        if search:
            # Search by first name, last name, or email
            query = query.or_(
                f"first_name.ilike.%{search}%,last_name.ilike.%{search}%,email.ilike.%{search}%"
            )

        if tag:
            # Filter array containing tag
            query = query.contains("tags", [tag])

        # Sort
        ascending = sort_order.lower() == "asc"
        query = query.order(sort_by, desc=not ascending)

        # Pagination
        start = (page - 1) * per_page
        end = start + per_page - 1
        query = query.range(start, end)

        response = query.execute()
        return response.data or [], response.count or 0

    def get_by_id(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Get customer by UUID."""
        response = (
            self.client.table("customers")
            .select("*")
            .eq("id", customer_id)
            .maybe_single()
            .execute()
        )
        return response.data

    def get_by_woo_id(self, woo_customer_id: int) -> Optional[Dict[str, Any]]:
        """Get customer by WooCommerce ID."""
        response = (
            self.client.table("customers")
            .select("*")
            .eq("woo_customer_id", woo_customer_id)
            .maybe_single()
            .execute()
        )
        return response.data

    def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get customer by email."""
        response = (
            self.client.table("customers")
            .select("*")
            .eq("email", email.strip().lower())
            .maybe_single()
            .execute()
        )
        return response.data

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a customer."""
        response = self.client.table("customers").insert(data).execute()
        return response.data[0]

    def upsert(self, data: Dict[str, Any], on_conflict: str = "woo_customer_id") -> Dict[str, Any]:
        """Upsert customer on conflict."""
        response = self.client.table("customers").upsert(data, on_conflict=on_conflict).execute()
        return response.data[0] if response.data else {}

    def upsert_from_woo(self, woo_customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Upsert customer from WooCommerce data.
        Conforms strictly to DATABASE.md section 9:
        insert into customers (woo_customer_id, email, first_name, last_name, phone, billing, shipping, synced_at)
        values (...)
        on conflict (email) do update set
          woo_customer_id = coalesce(excluded.woo_customer_id, customers.woo_customer_id),
          first_name = excluded.first_name,
          last_name = excluded.last_name,
          phone = excluded.phone,
          billing = excluded.billing,
          shipping = excluded.shipping,
          synced_at = now()
        returning id;
        """
        from app.services.woo_mapper import map_woo_customer_to_db

        mapped = map_woo_customer_to_db(woo_customer_data)
        email = mapped.get("email")
        if not email:
            raise ValueError("Customer must have a valid email to upsert")

        existing = self.get_by_email(email)
        if existing:
            # Preserves existing woo_customer_id if incoming is None (guest or omitted)
            woo_cust_id = (
                mapped["woo_customer_id"]
                if mapped.get("woo_customer_id") is not None
                else existing.get("woo_customer_id")
            )
            update_data = {
                "woo_customer_id": woo_cust_id,
                "first_name": mapped["first_name"] or existing.get("first_name", ""),
                "last_name": mapped["last_name"] or existing.get("last_name", ""),
                "phone": mapped["phone"] or existing.get("phone"),
                "billing": mapped["billing"] or existing.get("billing", {}),
                "shipping": mapped["shipping"] or existing.get("shipping", {}),
                "total_spent": mapped["total_spent"] if mapped.get("total_spent") else existing.get("total_spent", 0.0),
                "orders_count": mapped["orders_count"] if mapped.get("orders_count") else existing.get("orders_count", 0),
                "synced_at": mapped["synced_at"],
            }
            updated = self.update(existing["id"], update_data)
            return updated or existing
        else:
            return self.create(mapped)

    def refresh_customer_totals(self, customer_id: str) -> Dict[str, Any]:
        """
        Refresh customer orders_count and total_spent after an order upsert.
        Conforms to DATABASE.md section 9:
        update customers c set
          orders_count = s.cnt,
          total_spent  = s.total
        from (
          select customer_id, count(*) cnt, coalesce(sum(total), 0) total
          from orders
          where customer_id = $1 and status not in ('cancelled','failed','refunded')
          group by customer_id
        ) s
        where c.id = s.customer_id;
        """
        # Query orders not in ('cancelled', 'failed', 'refunded')
        resp = (
            self.client.table("orders")
            .select("total, status")
            .eq("customer_id", customer_id)
            .not_.in_("status", ["cancelled", "failed", "refunded"])
            .execute()
        )
        orders = resp.data or []
        cnt = len(orders)
        total = sum(float(o.get("total") or 0.0) for o in orders)

        updated = self.update(
            customer_id,
            {"orders_count": cnt, "total_spent": total},
        )
        return updated or {}

    def update(self, customer_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update customer details."""
        response = (
            self.client.table("customers")
            .update(data)
            .eq("id", customer_id)
            .execute()
        )
        return response.data[0] if response.data else None

    def create_note(self, customer_id: str, author_id: str, body: str) -> Dict[str, Any]:
        """Create a customer note."""
        note_data = {
            "customer_id": customer_id,
            "author_id": author_id,
            "body": body,
        }
        response = self.client.table("customer_notes").insert(note_data).execute()
        return response.data[0]

    def get_notes(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get all notes for a customer ordered by created_at desc."""
        response = (
            self.client.table("customer_notes")
            .select("*")
            .eq("customer_id", customer_id)
            .order("created_at", desc=True)
            .execute()
        )
        return response.data or []

    def get_orders(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get all orders for a customer."""
        response = (
            self.client.table("orders")
            .select("*")
            .eq("customer_id", customer_id)
            .order("placed_at", desc=True)
            .execute()
        )
        return response.data or []

    def get_communications(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get all communications for a customer."""
        response = (
            self.client.table("communications")
            .select("*")
            .eq("customer_id", customer_id)
            .order("created_at", desc=True)
            .execute()
        )
        return response.data or []

