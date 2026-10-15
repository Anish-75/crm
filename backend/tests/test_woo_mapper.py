from app.services.woo_mapper import (
    map_woo_customer_to_db,
    map_woo_order_items_to_db,
    map_woo_order_to_db,
)


def test_map_woo_customer_standard():
    woo_customer = {
        "id": 101,
        "email": "JOHN.DOE@Example.com",
        "first_name": "John",
        "last_name": "Doe",
        "billing": {
            "first_name": "John",
            "last_name": "Doe",
            "phone": "+1-555-0199",
            "city": "Austin",
        },
        "shipping": {"city": "Austin"},
        "total_spent": "249.99",
        "orders_count": "3",
    }
    mapped = map_woo_customer_to_db(woo_customer)
    assert mapped["woo_customer_id"] == 101
    assert mapped["email"] == "john.doe@example.com"
    assert mapped["first_name"] == "John"
    assert mapped["last_name"] == "Doe"
    assert mapped["phone"] == "+1-555-0199"
    assert mapped["billing"]["city"] == "Austin"
    assert mapped["total_spent"] == 249.99
    assert mapped["orders_count"] == 3
    assert "synced_at" in mapped


def test_map_woo_customer_guest():
    woo_guest = {
        "id": 0,
        "billing": {
            "first_name": "Jane",
            "last_name": "Guest",
            "email": "jane.guest@example.com",
            "phone": "+1-555-0100",
        },
    }
    mapped = map_woo_customer_to_db(woo_guest)
    assert mapped["woo_customer_id"] is None
    assert mapped["email"] == "jane.guest@example.com"
    assert mapped["first_name"] == "Jane"
    assert mapped["last_name"] == "Guest"
    assert mapped["phone"] == "+1-555-0100"
    assert mapped["total_spent"] == 0.0
    assert mapped["orders_count"] == 0


def test_map_woo_order():
    woo_order = {
        "id": 5001,
        "status": "Processing",
        "currency": "usd",
        "total": "99.50",
        "payment_method": "stripe",
        "billing": {"first_name": "Alice"},
        "shipping": {"city": "New York"},
        "date_created_gmt": "2026-10-15T10:00:00",
    }
    customer_id = "c0000000-0000-0000-0000-000000000001"
    mapped = map_woo_order_to_db(woo_order, customer_id=customer_id)

    assert mapped["woo_order_id"] == 5001
    assert mapped["customer_id"] == customer_id
    assert mapped["status"] == "processing"
    assert mapped["currency"] == "USD"
    assert mapped["total"] == 99.50
    assert mapped["payment_method"] == "stripe"
    assert mapped["placed_at"] == "2026-10-15T10:00:00"
    assert "synced_at" in mapped


def test_map_woo_order_items():
    line_items = [
        {
            "id": 11,
            "product_id": 201,
            "name": "Widget A",
            "sku": "WIDGET-A",
            "quantity": 2,
            "price": "19.99",
            "total": "39.98",
        },
        {
            "id": 12,
            "product_id": 0,
            "name": "Custom Service",
            "sku": "",
            "quantity": 1,
            "price": "50.00",
            "total": "50.00",
        },
    ]
    order_id = "o0000000-0000-0000-0000-000000000001"
    mapped = map_woo_order_items_to_db(line_items, order_id=order_id)

    assert len(mapped) == 2
    assert mapped[0]["order_id"] == order_id
    assert mapped[0]["woo_product_id"] == 201
    assert mapped[0]["sku"] == "WIDGET-A"
    assert mapped[0]["quantity"] == 2
    assert mapped[0]["price"] == 19.99
    assert mapped[0]["total"] == 39.98

    assert mapped[1]["woo_product_id"] is None
    assert mapped[1]["sku"] is None
    assert mapped[1]["quantity"] == 1
    assert mapped[1]["price"] == 50.0

