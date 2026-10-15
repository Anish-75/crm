from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    communications,
    customers,
    dashboard,
    health,
    orders,
    sync,
    templates,
    webhooks,
    workflows,
)

api_router = APIRouter()

# Health endpoints
api_router.include_router(health.router)

# Auth profile endpoint
api_router.include_router(auth.router)

# Core business domain endpoints
api_router.include_router(customers.router)
api_router.include_router(orders.router)
api_router.include_router(templates.router)
api_router.include_router(workflows.router)
api_router.include_router(communications.router)
api_router.include_router(dashboard.router)
api_router.include_router(sync.router)
api_router.include_router(webhooks.router)

