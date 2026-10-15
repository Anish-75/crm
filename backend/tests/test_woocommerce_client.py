import httpx
import pytest
import respx
from app.services.woocommerce_client import (
    WooCommerceClient,
    WooCommerceError,
    WooCommerceRateLimitError,
)

BASE_URL = "https://mock-woo-store.test"
CK = "ck_test_key_12345"
CS = "cs_test_secret_67890"


@pytest.fixture
def woo_client():
    client = WooCommerceClient(
        base_url=BASE_URL,
        consumer_key=CK,
        consumer_secret=CS,
        timeout=5.0,
        max_retries=2,
        backoff_factor=0.01,  # Fast backoff for tests
    )
    return client


@pytest.mark.asyncio
@respx.mock
async def test_list_customers_success(woo_client):
    mock_customers = [
        {"id": 1, "first_name": "Alice", "email": "alice@example.com"},
        {"id": 2, "first_name": "Bob", "email": "bob@example.com"},
    ]
    route = respx.get(f"{BASE_URL}/wp-json/wc/v3/customers").respond(
        status_code=200,
        json=mock_customers,
        headers={"X-WP-TotalPages": "5", "X-WP-Total": "10"},
    )

    async with woo_client as client:
        items, total_pages = await client.list_customers(page=1, per_page=100)

    assert route.called
    assert len(items) == 2
    assert total_pages == 5
    assert items[0]["email"] == "alice@example.com"


@pytest.mark.asyncio
@respx.mock
async def test_list_orders_success(woo_client):
    mock_orders = [
        {"id": 100, "status": "processing", "total": "50.00"},
    ]
    route = respx.get(f"{BASE_URL}/wp-json/wc/v3/orders").respond(
        status_code=200,
        json=mock_orders,
        headers={"X-WP-TotalPages": "2", "X-WP-Total": "2"},
    )

    async with woo_client as client:
        result = await client.list_orders(page=1, per_page=100, status="processing")

    assert route.called
    assert len(result.items) == 1
    assert result.total_pages == 2
    assert result.total_count == 2
    assert result.items[0]["id"] == 100


@pytest.mark.asyncio
@respx.mock
async def test_get_order_success(woo_client):
    mock_order = {"id": 100, "status": "completed", "total": "75.00"}
    route = respx.get(f"{BASE_URL}/wp-json/wc/v3/orders/100").respond(
        status_code=200,
        json=mock_order,
    )

    async with woo_client as client:
        order = await client.get_order(100)

    assert route.called
    assert order["id"] == 100
    assert order["status"] == "completed"


@pytest.mark.asyncio
@respx.mock
async def test_update_order_status_success(woo_client):
    mock_updated = {"id": 100, "status": "completed"}
    route = respx.put(f"{BASE_URL}/wp-json/wc/v3/orders/100").respond(
        status_code=200,
        json=mock_updated,
    )

    async with woo_client as client:
        result = await client.update_order_status(100, "completed")

    assert route.called
    assert result["status"] == "completed"


@pytest.mark.asyncio
@respx.mock
async def test_rate_limit_429_retry_success(woo_client):
    """Should retry upon 429 and succeed if subsequent attempt passes."""
    route = respx.get(f"{BASE_URL}/wp-json/wc/v3/customers")
    route.side_effect = [
        httpx.Response(429, headers={"Retry-After": "0.01"}),
        httpx.Response(
            200,
            json=[{"id": 1, "email": "retry@example.com"}],
            headers={"X-WP-TotalPages": "1"},
        ),
    ]

    async with woo_client as client:
        items, pages = await client.list_customers()

    assert route.call_count == 2
    assert len(items) == 1
    assert items[0]["email"] == "retry@example.com"


@pytest.mark.asyncio
@respx.mock
async def test_rate_limit_429_exhausted(woo_client):
    """Should raise WooCommerceRateLimitError when retries are exhausted."""
    route = respx.get(f"{BASE_URL}/wp-json/wc/v3/customers").respond(
        status_code=429,
        headers={"Retry-After": "0.01"},
    )

    with pytest.raises(WooCommerceRateLimitError):
        async with woo_client as client:
            await client.list_customers()

    assert route.call_count == woo_client.max_retries + 1


@pytest.mark.asyncio
@respx.mock
async def test_server_error_500_retry_and_exhausted(woo_client):
    """Should retry 5xx errors and raise WooCommerceError when exhausted."""
    route = respx.get(f"{BASE_URL}/wp-json/wc/v3/orders/100").respond(status_code=500)

    with pytest.raises(WooCommerceError) as exc_info:
        async with woo_client as client:
            await client.get_order(100)

    assert exc_info.value.status_code == 500
    assert route.call_count == woo_client.max_retries + 1


@pytest.mark.asyncio
@respx.mock
async def test_client_error_404_no_retry(woo_client):
    """Client errors (e.g. 404) should fail immediately without retrying."""
    route = respx.get(f"{BASE_URL}/wp-json/wc/v3/orders/999").respond(
        status_code=404,
        json={"message": "Order not found"},
    )

    with pytest.raises(WooCommerceError) as exc_info:
        async with woo_client as client:
            await client.get_order(999)

    assert exc_info.value.status_code == 404
    assert route.call_count == 1  # No retries on 404


@pytest.mark.asyncio
@respx.mock
async def test_paginate_all_customers_generator(woo_client):
    """Test paginate_all_customers yields pages until total_pages reached."""
    route = respx.get(f"{BASE_URL}/wp-json/wc/v3/customers")
    route.side_effect = [
        httpx.Response(
            200,
            json=[{"id": 1}, {"id": 2}],
            headers={"X-WP-TotalPages": "2"},
        ),
        httpx.Response(
            200,
            json=[{"id": 3}],
            headers={"X-WP-TotalPages": "2"},
        ),
    ]

    all_pages = []
    async with woo_client as client:
        async for page_items in client.paginate_all_customers(per_page=2):
            all_pages.append(page_items)

    assert len(all_pages) == 2
    assert len(all_pages[0]) == 2
    assert len(all_pages[1]) == 1

