from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def map_woo_customer_to_db(woo_customer: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map WooCommerce customer JSON payload to the database `customers` schema.
    Conforms to DATABASE.md section 9 and PRD section 5/6.
    """
    raw_id = woo_customer.get("id")
    woo_customer_id = int(raw_id) if raw_id is not None and int(raw_id) > 0 else None

    billing = woo_customer.get("billing") or {}
    shipping = woo_customer.get("shipping") or {}

    email = (
        woo_customer.get("email")
        or billing.get("email")
        or ""
    ).strip().lower()

    first_name = (
        woo_customer.get("first_name")
        or billing.get("first_name")
        or ""
    ).strip()

    last_name = (
        woo_customer.get("last_name")
        or billing.get("last_name")
        or ""
    ).strip()

    phone = billing.get("phone") or woo_customer.get("phone") or None

    try:
        total_spent = float(woo_customer.get("total_spent", 0.0) or 0.0)
    except (ValueError, TypeError):
        total_spent = 0.0

    try:
        orders_count = int(woo_customer.get("orders_count", 0) or 0)
    except (ValueError, TypeError):
        orders_count = 0

    return {
        "woo_customer_id": woo_customer_id,
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "phone": phone,
        "billing": billing,
        "shipping": shipping,
        "total_spent": total_spent,
        "orders_count": orders_count,
        "synced_at": datetime.now(timezone.utc).isoformat(),
    }


def map_woo_order_to_db(
    woo_order: Dict[str, Any],
    customer_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Map WooCommerce order JSON payload to the database `orders` schema.
    Conforms to DATABASE.md section 9 and PRD section 5/6.
    """
    woo_order_id = int(woo_order["id"])
    status = str(woo_order.get("status", "pending")).lower()
    currency = str(woo_order.get("currency", "USD")).upper()

    try:
        total = float(woo_order.get("total", 0.0) or 0.0)
    except (ValueError, TypeError):
        total = 0.0

    payment_method = (
        woo_order.get("payment_method")
        or woo_order.get("payment_method_title")
        or None
    )

    billing = woo_order.get("billing") or {}
    shipping = woo_order.get("shipping") or {}

    placed_at = (
        woo_order.get("date_created_gmt")
        or woo_order.get("date_created")
        or datetime.now(timezone.utc).isoformat()
    )

    return {
        "woo_order_id": woo_order_id,
        "customer_id": customer_id,
        "status": status,
        "currency": currency,
        "total": total,
        "payment_method": payment_method,
        "billing": billing,
        "shipping": shipping,
        "placed_at": placed_at,
        "synced_at": datetime.now(timezone.utc).isoformat(),
    }


def map_woo_order_items_to_db(
    line_items: List[Dict[str, Any]],
    order_id: str,
) -> List[Dict[str, Any]]:
    """
    Map WooCommerce line items from order JSON to the `order_items` schema.
    Conforms to DATABASE.md section 9.
    """
    mapped_items = []
    for item in line_items:
        raw_product_id = item.get("product_id")
        woo_product_id = int(raw_product_id) if raw_product_id is not None and int(raw_product_id) > 0 else None

        try:
            quantity = max(1, int(item.get("quantity", 1) or 1))
        except (ValueError, TypeError):
            quantity = 1

        try:
            price = float(item.get("price", 0.0) or 0.0)
        except (ValueError, TypeError):
            price = 0.0

        try:
            total = float(item.get("total", 0.0) or 0.0)
        except (ValueError, TypeError):
            total = 0.0

        mapped_items.append(
            {
                "order_id": order_id,
                "woo_product_id": woo_product_id,
                "name": item.get("name") or "Item",
                "sku": item.get("sku") or None,
                "quantity": quantity,
                "price": price,
                "total": total,
            }
        )
    return mapped_items

