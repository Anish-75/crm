from typing import Any, Dict, List, Optional, Tuple
from app.core.exceptions import NotFoundError
from app.repositories.customer_repo import CustomerRepository
from app.schemas.customer import CustomerNoteCreate, CustomerUpdate


class CustomerService:
    """Service handling customer business logic."""

    def __init__(self, customer_repo: Optional[CustomerRepository] = None):
        self.customer_repo = customer_repo or CustomerRepository()

    def list_customers(
        self,
        search: Optional[str] = None,
        tag: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Tuple[List[Dict[str, Any]], int]:
        return self.customer_repo.list_customers(
            search=search,
            tag=tag,
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    def get_customer(self, customer_id: str) -> Dict[str, Any]:
        customer = self.customer_repo.get_by_id(customer_id)
        if not customer:
            raise NotFoundError(f"Customer with ID {customer_id} not found")
        return customer

    def update_customer(self, customer_id: str, update_data: CustomerUpdate) -> Dict[str, Any]:
        payload = update_data.model_dump(exclude_unset=True)
        updated = self.customer_repo.update(customer_id, payload)
        if not updated:
            raise NotFoundError(f"Customer with ID {customer_id} not found")
        return updated

    def add_note(self, customer_id: str, author_id: str, note_data: CustomerNoteCreate) -> Dict[str, Any]:
        # Verify customer exists
        self.get_customer(customer_id)
        return self.customer_repo.create_note(customer_id, author_id, note_data.body)

    def get_notes(self, customer_id: str) -> List[Dict[str, Any]]:
        self.get_customer(customer_id)
        return self.customer_repo.get_notes(customer_id)

    def get_orders(self, customer_id: str) -> List[Dict[str, Any]]:
        self.get_customer(customer_id)
        return self.customer_repo.get_orders(customer_id)

    def get_communications(self, customer_id: str) -> List[Dict[str, Any]]:
        self.get_customer(customer_id)
        return self.customer_repo.get_communications(customer_id)

