import hashlib
import hmac
import logging
from typing import Optional
from fastapi import APIRouter, Header, HTTPException, Request, status
from app.config import get_settings
from app.repositories.sync_repo import SyncRepository
from app.schemas.webhook import WebhookResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Webhooks"])


@router.post(
    "/webhooks/woocommerce",
    response_model=WebhookResponse,
    status_code=status.HTTP_200_OK,
    summary="WooCommerce Webhook receiver",
)
async def woocommerce_webhook(
    request: Request,
    x_wc_webhook_signature: Optional[str] = Header(None, alias="X-WC-Webhook-Signature"),
    x_wc_webhook_topic: Optional[str] = Header(None, alias="X-WC-Webhook-Topic"),
    x_wc_webhook_delivery_id: Optional[str] = Header(None, alias="X-WC-Webhook-Delivery-ID"),
) -> WebhookResponse:
    """
    Receives WooCommerce webhooks.
    - Public route (no Supabase JWT required).
    - Verifies HMAC-SHA256 signature using WOO_WEBHOOK_SECRET.
    - Deduplicates using X-WC-Webhook-Delivery-ID.
    """
    settings = get_settings()
    raw_body = await request.body()

    # If secret is set, verify HMAC signature (PRD Section 6)
    if settings.WOO_WEBHOOK_SECRET:
        if not x_wc_webhook_signature:
            logger.warning("Missing WooCommerce webhook signature header")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing webhook signature",
            )

        expected_signature = hmac.new(
            settings.WOO_WEBHOOK_SECRET.encode("utf-8"),
            raw_body,
            hashlib.sha256,
        ).digest()
        import base64
        expected_b64 = base64.b64encode(expected_signature).decode("utf-8")

        if not hmac.compare_digest(expected_b64, x_wc_webhook_signature):
            logger.warning("Invalid WooCommerce webhook signature")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature",
            )

    # Check deduplication if delivery ID provided
    sync_repo = SyncRepository()
    if x_wc_webhook_delivery_id:
        existing = sync_repo.get_webhook_event(x_wc_webhook_delivery_id)
        if existing:
            logger.info(f"Deduplicated webhook event {x_wc_webhook_delivery_id}")
            return WebhookResponse(
                received=True,
                delivery_id=x_wc_webhook_delivery_id,
                topic=x_wc_webhook_topic,
                message="Duplicate webhook event ignored",
            )

    # Record webhook event (background processing in Phase 3)
    try:
        import json
        payload = json.loads(raw_body.decode("utf-8")) if raw_body else {}
        if x_wc_webhook_delivery_id:
            sync_repo.record_webhook_event(
                woo_delivery_id=x_wc_webhook_delivery_id,
                topic=x_wc_webhook_topic or "unknown",
                payload=payload,
                processed=False,
            )
    except Exception as e:
        logger.error(f"Failed to record webhook event: {e}")

    return WebhookResponse(
        received=True,
        delivery_id=x_wc_webhook_delivery_id,
        topic=x_wc_webhook_topic,
        message="Webhook acknowledged",
    )

