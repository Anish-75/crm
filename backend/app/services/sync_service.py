from typing import Any, Dict, List, Optional
from app.repositories.sync_repo import SyncRepository
from app.schemas.sync import SyncType


class SyncService:
    """Service handling synchronization status and trigger."""

    def __init__(self, sync_repo: Optional[SyncRepository] = None):
        self.sync_repo = sync_repo or SyncRepository()

    def get_sync_status(self) -> Dict[str, Any]:
        latest = self.sync_repo.get_latest_sync()
        recent = self.sync_repo.get_recent_logs(limit=10)
        return {
            "is_syncing": False,  # Will be wired to background task flag in Phase 2
            "last_sync": latest,
            "recent_logs": recent,
        }

    def trigger_sync(self, sync_type: SyncType = SyncType.FULL) -> Dict[str, Any]:
        # Log initiation of sync (full import logic implemented in Phase 2)
        log_entry = {
            "type": sync_type.value,
            "resource": "all",
            "status": "success",
            "details": {"message": "Sync queued/completed successfully"},
        }
        return self.sync_repo.create_log(log_entry)

