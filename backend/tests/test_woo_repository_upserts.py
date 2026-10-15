from unittest.mock import MagicMock
from app.repositories.customer_repo import CustomerRepository
from app.repositories.order_repo import OrderRepository


def test_customer_repo_upsert_new_customer():
    mock_client = MagicMock()
    customer_repo = CustomerRepository(client=mock_client)

    # Mock get_by_email returning None
    get_exec = MagicMock()
    get_exec.data = None
    mock_client.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = get_exec

    # Mock insert returning created customer
    created_cust = {
        "id": "c0000000-0000-0000-0000-000000000001",
        "woo_customer_id": 10,
        "email": "new@example.com",
        "first_name": "New",
        "last_name": "User",
        "phone": "+123456789",
        "billing": {},
        "shipping": {},
        "total_spent": 0.0,
        "orders_count": 0,
        "synced_at": "2026-10-15T12:00:00Z",
    }
    insert_exec = MagicMock()
    insert_exec.data = [created_cust]
    mock_client.table.return_value.insert.return_value.execute.return_value = insert_exec

    woo_data = {
        "id": 10,
        "email": "NEW@Example.com",
        "first_name": "New",
        "last_name": "User",
        "phone": "+123456789",
    }
    result = customer_repo.upsert_from_woo(woo_data)

    assert result["id"] == "c0000000-0000-0000-0000-000000000001"
    assert result["email"] == "new@example.com"


def test_customer_repo_upsert_existing_customer_preserves_woo_id():
    mock_client = MagicMock()
    customer_repo = CustomerRepository(client=mock_client)

    # Existing customer in DB has woo_customer_id = 99
    existing = {
        "id": "c0000000-0000-0000-0000-000000000002",
        "woo_customer_id": 99,
        "email": "existing@example.com",
        "first_name": "Old",
        "last_name": "Name",
        "phone": None,
        "billing": {},
        "shipping": {},
        "total_spent": 100.0,
        "orders_count": 1,
    }
    get_exec = MagicMock()
    get_exec.data = existing
    mock_client.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value = get_exec

    # Mock update
    def mock_update_execute(*args, **kwargs):
        return MagicMock(data=[{**existing, "first_name": "Updated"}])

    mock_client.table.return_value.update.return_value.eq.return_value.execute.side_effect = mock_update_execute

    # Incoming data has no woo_customer_id (e.g. guest order by this email)
    woo_data = {
        "id": 0,
        "email": "existing@example.com",
        "first_name": "Updated",
        "last_name": "Name",
    }
    result = customer_repo.upsert_from_woo(woo_data)

    # Check that update was called with preserved woo_customer_id = 99 (coalesce behavior)
    update_call_args = mock_client.table.return_value.update.call_args[0][0]
    assert update_call_args["woo_customer_id"] == 99
    assert update_call_args["first_name"] == "Updated"


def test_customer_repo_refresh_customer_totals():
    mock_client = MagicMock()
    customer_repo = CustomerRepository(client=mock_client)

    # Mock orders query returning 2 completed orders and filtering out cancelled/failed
    orders_exec = MagicMock()
    orders_exec.data = [
        {"total": 50.0, "status": "completed"},
        {"total": 75.50, "status": "processing"},
    ]
    mock_client.table.return_value.select.return_value.eq.return_value.not_.in_.return_value.execute.return_value = orders_exec

    # Mock update returning updated customer
    update_exec = MagicMock()
    update_exec.data = [{"id": "c1", "orders_count": 2, "total_spent": 125.50}]
    mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value = update_exec

    result = customer_repo.refresh_customer_totals("c1")

    update_payload = mock_client.table.return_value.update.call_args[0][0]
    assert update_payload["orders_count"] == 2
    assert update_payload["total_spent"] == 125.50


def test_order_repo_upsert_order_status_history_on_diff():
    mock_client = MagicMock()
    order_repo = OrderRepository(client=mock_client)

    # 1. Existing order has status "processing"
    existing_order = {
        "id": "o1",
        "woo_order_id": 200,
        "status": "processing",
        "customer_id": "c1",
    }

    # Setup get_by_woo_id
    select_builder = MagicMock()
    select_builder.eq.return_value.maybe_single.return_value.execute.return_value = MagicMock(data=existing_order)
    select_builder.not_.in_.return_value.execute.return_value = MagicMock(data=[])

    mock_client.table.return_value.select.return_value = select_builder
    mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[{**existing_order, "status": "completed"}]
    )
    mock_client.table.return_value.delete.return_value.eq.return_value.execute.return_value = MagicMock()
    mock_client.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[])

    woo_order = {
        "id": 200,
        "status": "completed",
        "currency": "USD",
        "total": "99.00",
        "line_items": [
            {"product_id": 5, "name": "Book", "quantity": 1, "price": 99.00, "total": 99.00}
        ],
    }

    result = order_repo.upsert_from_woo(woo_order, customer_id="c1")

    # Verify order_status_history was recorded with from_status='processing' and to_status='completed'
    insert_calls = [
        call[0][0]
        for call in mock_client.table("order_status_history").insert.call_args_list
    ]
    status_history_inserts = [
        call for call in insert_calls if isinstance(call, dict) and "to_status" in call
    ]
    assert len(status_history_inserts) == 1
    assert status_history_inserts[0]["from_status"] == "processing"
    assert status_history_inserts[0]["to_status"] == "completed"
    assert status_history_inserts[0]["source"] == "woo"


def test_order_repo_upsert_order_no_history_when_same_status():
    mock_client = MagicMock()
    order_repo = OrderRepository(client=mock_client)

    # Existing order already has status "completed"
    existing_order = {
        "id": "o1",
        "woo_order_id": 200,
        "status": "completed",
        "customer_id": "c1",
    }

    select_builder = MagicMock()
    select_builder.eq.return_value.maybe_single.return_value.execute.return_value = MagicMock(data=existing_order)
    select_builder.not_.in_.return_value.execute.return_value = MagicMock(data=[])

    mock_client.table.return_value.select.return_value = select_builder
    mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[existing_order]
    )
    mock_client.table.return_value.delete.return_value.eq.return_value.execute.return_value = MagicMock()
    mock_client.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[])

    woo_order = {
        "id": 200,
        "status": "completed",
        "currency": "USD",
        "total": "99.00",
        "line_items": [],
    }

    result = order_repo.upsert_from_woo(woo_order, customer_id="c1")

    # Status did NOT change ('completed' == 'completed'), so no status history row should be created
    status_history_calls = [
        call
        for call in mock_client.table("order_status_history").insert.call_args_list
        if call[0] and isinstance(call[0][0], dict) and "to_status" in call[0][0]
    ]
    assert len(status_history_calls) == 0

