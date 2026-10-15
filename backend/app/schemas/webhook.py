from typing import Optional
from pydantic import BaseModel


class WebhookResponse(BaseModel):
    received: bool = True
    delivery_id: Optional[str] = None
    topic: Optional[str] = None
    message: str = "Webhook received successfully"

