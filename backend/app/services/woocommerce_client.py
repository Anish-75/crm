import asyncio
import logging
from typing import Any, AsyncGenerator, Dict, List, NamedTuple, Optional, Tuple
import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


class WooCommerceError(Exception):
    """Base exception for WooCommerce API errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_body: Optional[Any] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_body = response_body


class WooCommerceRateLimitError(WooCommerceError):
    """Raised when WooCommerce rate limit (HTTP 429) is exceeded after retries."""
    pass


class WooPagedResult(NamedTuple):
    """
    Paged result containing records, total pages, and total count.
    Unpacks as `(items, total_pages)` for tuple compatibility.
    """
    items: List[Dict[str, Any]]
    total_pages: int
    total_count: int

    def __iter__(self):
        # Support unpacking as: items, total_pages = await client.list_customers()
        yield self.items
        yield self.total_pages


class WooCommerceClient:
    """
    Async WooCommerce REST API v3 client using httpx.
    Implements Basic Auth, timeouts, exponential backoff retries on 429 & 5xx,
    and pagination via the X-WP-TotalPages header (PRD Section 6).
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        consumer_key: Optional[str] = None,
        consumer_secret: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        backoff_factor: float = 0.5,
        client: Optional[httpx.AsyncClient] = None,
    ):
        settings = get_settings()
        self.base_url = (base_url or settings.WOO_BASE_URL).rstrip("/")
        self.consumer_key = consumer_key or settings.WOO_CONSUMER_KEY
        self.consumer_secret = consumer_secret or settings.WOO_CONSUMER_SECRET
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

        self._external_client = client is not None
        self._client: Optional[httpx.AsyncClient] = client

    async def _get_client(self) -> httpx.AsyncClient:
        """Initialize or return internal async httpx client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout, connect=10.0),
                auth=httpx.BasicAuth(self.consumer_key, self.consumer_secret),
                headers={
                    "Accept": "application/json",
                    "User-Agent": "WooCommerce-CRM-Sync/1.0",
                },
            )
        return self._client

    async def close(self) -> None:
        """Close the underlying HTTP client session."""
        if not self._external_client and self._client is not None and not self._client.is_closed:
            await self._client.aclose()

    async def __aenter__(self) -> "WooCommerceClient":
        await self._get_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    def _build_url(self, endpoint: str) -> str:
        """Construct full WooCommerce v3 API URL."""
        endpoint = endpoint.lstrip("/")
        return f"{self.base_url}/wp-json/wc/v3/{endpoint}"

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        """
        Execute an HTTP request with exponential backoff and error handling for 429 and 5xx.
        """
        client = await self._get_client()
        url = self._build_url(endpoint)

        # Filter out None params
        cleaned_params = {k: v for k, v in (params or {}).items() if v is not None}

        for attempt in range(self.max_retries + 1):
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    params=cleaned_params,
                    json=json_data,
                )

                # HTTP 429 - Rate limit handling
                if response.status_code == 429:
                    if attempt == self.max_retries:
                        logger.error(f"WooCommerce rate limit (429) exceeded after {self.max_retries} retries: {url}")
                        raise WooCommerceRateLimitError(
                            "WooCommerce API rate limit exceeded",
                            status_code=429,
                            response_body=response.text,
                        )

                    retry_after = response.headers.get("Retry-After")
                    try:
                        delay = float(retry_after) if retry_after else (self.backoff_factor * (2 ** attempt))
                    except (ValueError, TypeError):
                        delay = self.backoff_factor * (2 ** attempt)

                    logger.warning(
                        f"WooCommerce rate limited (429). Retrying in {delay:.2f}s (attempt {attempt + 1}/{self.max_retries})"
                    )
                    await asyncio.sleep(delay)
                    continue

                # HTTP 5xx - Server error handling
                if 500 <= response.status_code < 600:
                    if attempt == self.max_retries:
                        logger.error(
                            f"WooCommerce server error {response.status_code} after {self.max_retries} retries: {url}"
                        )
                        raise WooCommerceError(
                            f"WooCommerce server error: HTTP {response.status_code}",
                            status_code=response.status_code,
                            response_body=response.text,
                        )

                    delay = self.backoff_factor * (2 ** attempt)
                    logger.warning(
                        f"WooCommerce 5xx error ({response.status_code}). Retrying in {delay:.2f}s (attempt {attempt + 1}/{self.max_retries})"
                    )
                    await asyncio.sleep(delay)
                    continue

                # HTTP 4xx - Client errors (do not retry, raise immediately)
                if response.is_error:
                    error_msg = f"WooCommerce API error: {response.status_code} {response.reason_phrase}"
                    try:
                        body = response.json()
                        if isinstance(body, dict) and "message" in body:
                            error_msg = f"WooCommerce API error: {body['message']}"
                    except Exception:
                        body = response.text

                    logger.error(f"{error_msg} on {method} {url}")
                    raise WooCommerceError(
                        error_msg,
                        status_code=response.status_code,
                        response_body=body,
                    )

                return response

            except (httpx.ConnectError, httpx.ReadTimeout, httpx.WriteTimeout, httpx.PoolTimeout) as exc:
                if attempt == self.max_retries:
                    logger.error(f"Network error communicating with WooCommerce after {self.max_retries} retries: {exc}")
                    raise WooCommerceError(
                        f"Network error communicating with WooCommerce: {type(exc).__name__}",
                    ) from exc

                delay = self.backoff_factor * (2 ** attempt)
                logger.warning(
                    f"Network error ({type(exc).__name__}). Retrying in {delay:.2f}s (attempt {attempt + 1}/{self.max_retries})"
                )
                await asyncio.sleep(delay)

        raise WooCommerceError("Unexpected error completing WooCommerce request")

    async def list_customers(
        self,
        page: int = 1,
        per_page: int = 100,
        modified_after: Optional[str] = None,
        search: Optional[str] = None,
        role: str = "all",
        **params: Any,
    ) -> WooPagedResult:
        """
        List WooCommerce customers with pagination.
        Reads X-WP-TotalPages and X-WP-Total headers.
        """
        query_params = {
            "page": page,
            "per_page": per_page,
            "role": role,
            **params,
        }
        if modified_after:
            query_params["modified_after"] = modified_after
        if search:
            query_params["search"] = search

        response = await self._request("GET", "customers", params=query_params)
        data = response.json() or []

        try:
            total_pages = int(response.headers.get("X-WP-TotalPages", 1))
        except (ValueError, TypeError):
            total_pages = 1

        try:
            total_count = int(response.headers.get("X-WP-Total", len(data)))
        except (ValueError, TypeError):
            total_count = len(data)

        return WooPagedResult(items=data, total_pages=total_pages, total_count=total_count)

    async def get_customer(self, woo_customer_id: int) -> Dict[str, Any]:
        """Fetch a single customer by WooCommerce ID."""
        response = await self._request("GET", f"customers/{woo_customer_id}")
        return response.json()

    async def list_orders(
        self,
        page: int = 1,
        per_page: int = 100,
        status: Optional[str] = None,
        modified_after: Optional[str] = None,
        customer_id: Optional[int] = None,
        **params: Any,
    ) -> WooPagedResult:
        """
        List WooCommerce orders with pagination.
        Reads X-WP-TotalPages and X-WP-Total headers.
        """
        query_params = {
            "page": page,
            "per_page": per_page,
            **params,
        }
        if status:
            query_params["status"] = status
        if modified_after:
            query_params["modified_after"] = modified_after
        if customer_id is not None:
            query_params["customer"] = customer_id

        response = await self._request("GET", "orders", params=query_params)
        data = response.json() or []

        try:
            total_pages = int(response.headers.get("X-WP-TotalPages", 1))
        except (ValueError, TypeError):
            total_pages = 1

        try:
            total_count = int(response.headers.get("X-WP-Total", len(data)))
        except (ValueError, TypeError):
            total_count = len(data)

        return WooPagedResult(items=data, total_pages=total_pages, total_count=total_count)

    async def get_order(self, woo_order_id: int) -> Dict[str, Any]:
        """Fetch a single order by WooCommerce ID."""
        response = await self._request("GET", f"orders/{woo_order_id}")
        return response.json()

    async def update_order_status(self, woo_order_id: int, status: str) -> Dict[str, Any]:
        """Update an order's status in WooCommerce."""
        response = await self._request(
            "PUT",
            f"orders/{woo_order_id}",
            json_data={"status": status},
        )
        return response.json()

    async def paginate_all_customers(
        self,
        per_page: int = 100,
        modified_after: Optional[str] = None,
    ) -> AsyncGenerator[List[Dict[str, Any]], None]:
        """Yield customer pages iteratively using X-WP-TotalPages."""
        page = 1
        total_pages = 1
        while page <= total_pages:
            result = await self.list_customers(
                page=page,
                per_page=per_page,
                modified_after=modified_after,
            )
            total_pages = result.total_pages
            if not result.items:
                break
            yield result.items
            page += 1

    async def paginate_all_orders(
        self,
        per_page: int = 100,
        status: Optional[str] = None,
        modified_after: Optional[str] = None,
    ) -> AsyncGenerator[List[Dict[str, Any]], None]:
        """Yield order pages iteratively using X-WP-TotalPages."""
        page = 1
        total_pages = 1
        while page <= total_pages:
            result = await self.list_orders(
                page=page,
                per_page=per_page,
                status=status,
                modified_after=modified_after,
            )
            total_pages = result.total_pages
            if not result.items:
                break
            yield result.items
            page += 1

