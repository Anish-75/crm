from typing import Any, Dict
from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_user
from app.schemas.auth import CurrentUser
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def get_dashboard_service() -> DashboardService:
    return DashboardService()


@router.get("/stats", response_model=Dict[str, Any], summary="Get dashboard KPIs and statistics")
async def get_dashboard_stats(
    current_user: CurrentUser = Depends(get_current_user),
    service: DashboardService = Depends(get_dashboard_service),
) -> Dict[str, Any]:
    """Retrieve overview metrics: revenue, order count, orders by status, and top customers."""
    return service.get_dashboard_stats()

