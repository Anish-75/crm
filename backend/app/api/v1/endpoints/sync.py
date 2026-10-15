from fastapi import APIRouter, Depends, status
from app.core.dependencies import require_admin
from app.schemas.auth import CurrentUser
from app.schemas.sync import (
    SyncLogResponse,
    SyncStatusResponse,
    SyncTriggerRequest,
    SyncType,
)
from app.services.sync_service import SyncService

router = APIRouter(prefix="/sync", tags=["Sync"])


def get_sync_service() -> SyncService:
    return SyncService()


@router.post(
    "/full",
    response_model=SyncLogResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger full sync from WooCommerce (Admin only)",
)
async def trigger_full_sync(
    req: SyncTriggerRequest = SyncTriggerRequest(type=SyncType.FULL),
    admin_user: CurrentUser = Depends(require_admin),
    service: SyncService = Depends(get_sync_service),
) -> SyncLogResponse:
    """Trigger a full import of WooCommerce customers and orders."""
    log = service.trigger_sync(sync_type=req.type)
    return SyncLogResponse.model_validate(log)


@router.get("/status", response_model=SyncStatusResponse, summary="Get sync status and logs (Admin only)")
async def get_sync_status(
    admin_user: CurrentUser = Depends(require_admin),
    service: SyncService = Depends(get_sync_service),
) -> SyncStatusResponse:
    """Check sync progress and recent sync events."""
    data = service.get_sync_status()
    return SyncStatusResponse.model_validate(data)

