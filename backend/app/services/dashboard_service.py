from typing import Any, Dict, Optional
from app.repositories.dashboard_repo import DashboardRepository


class DashboardService:
    """Service handling dashboard KPI calculation."""

    def __init__(self, dashboard_repo: Optional[DashboardRepository] = None):
        self.dashboard_repo = dashboard_repo or DashboardRepository()

    def get_dashboard_stats(self) -> Dict[str, Any]:
        return self.dashboard_repo.get_stats()

