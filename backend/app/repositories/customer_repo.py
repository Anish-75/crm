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

