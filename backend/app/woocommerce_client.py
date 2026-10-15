"""
Re-export WooCommerceClient and error classes from app.services.woocommerce_client
to satisfy imports directly from app.woocommerce_client (PRD Section 6).
"""
from app.services.woocommerce_client import (
    WooCommerceClient,
    WooCommerceError,
    WooCommerceRateLimitError,
    WooPagedResult,
)
from app.services.woo_mapper import (
    map_woo_customer_to_db,
    map_woo_order_items_to_db,
    map_woo_order_to_db,
)

__all__ = [
    "WooCommerceClient",
    "WooCommerceError",
    "WooCommerceRateLimitError",
    "WooPagedResult",
    "map_woo_customer_to_db",
    "map_woo_order_to_db",
    "map_woo_order_items_to_db",
]

