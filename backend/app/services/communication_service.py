from typing import Any, Dict, List, Optional, Tuple
from app.core.exceptions import NotFoundError, ValidationError
from app.repositories.communication_repo import CommunicationRepository
from app.repositories.customer_repo import CustomerRepository
from app.repositories.template_repo import TemplateRepository
from app.schemas.communication import CommunicationSendRequest


class CommunicationService:
    """Service handling email communication logging and sending."""

    def __init__(
        self,
        comm_repo: Optional[CommunicationRepository] = None,
        customer_repo: Optional[CustomerRepository] = None,
        template_repo: Optional[TemplateRepository] = None,
    ):
        self.comm_repo = comm_repo or CommunicationRepository()
        self.customer_repo = customer_repo or CustomerRepository()
        self.template_repo = template_repo or TemplateRepository()

    def list_communications(
        self,
        customer_id: Optional[str] = None,
        order_id: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> Tuple[List[Dict[str, Any]], int]:
        return self.comm_repo.list_communications(
            customer_id=customer_id,
            order_id=order_id,
            status=status,
            page=page,
            per_page=per_page,
        )

    def send_communication(self, req: CommunicationSendRequest) -> Dict[str, Any]:
        # 1. Verify customer exists
        customer = self.customer_repo.get_by_id(req.customer_id)
        if not customer:
            raise NotFoundError(f"Customer with ID {req.customer_id} not found")

        subject = req.subject
        body = req.body

        # 2. If template_id provided, fetch template
        if req.template_id:
            template = self.template_repo.get_by_id(req.template_id)
            if not template:
                raise NotFoundError(f"Template with ID {req.template_id} not found")
            subject = subject or template.get("subject")
            body = body or template.get("body_html")

        if not subject or not body:
            raise ValidationError("Subject and body are required directly or via a template")

        # 3. Queue communication record in DB
        comm_data = {
            "customer_id": req.customer_id,
            "order_id": req.order_id,
            "template_id": req.template_id,
            "channel": "email",
            "subject": subject,
            "body": body,
            "status": "queued",
        }
        return self.comm_repo.create(comm_data)

