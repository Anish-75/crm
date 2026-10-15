# PRD: WooCommerce-Integrated CRM

> Instructions for the AI agent: build this project phase by phase. Finish and verify each phase before starting the next. Ask before changing the stack or schema. Never commit secrets.

## 1. Overview
A Customer Relationship Management system that integrates with a WooCommerce store. It syncs customers and orders from WooCommerce, lets staff manage customer data and track orders, and runs email communication workflows triggered by order events.

**Challenge scope:** (1) customer data management, (2) order tracking, (3) communication workflows.

## 2. Tech Stack
| Layer | Choice |
|---|---|
| Backend | FastAPI (Python 3.11+), Pydantic v2, httpx, APScheduler |
| Database / Auth | Supabase (Postgres + Supabase Auth + RLS) |
| Frontend | React + Vite + TypeScript, React Router, TanStack Query, Tailwind CSS |
| Email | Resend or SMTP (configurable) |
| Testing | pytest, respx (HTTP mocking), React Testing Library, Playwright (one E2E flow) |
| Deployment | Docker + docker-compose (backend), env-based config |

## 3. Architecture
```
WooCommerce --(webhooks)--> FastAPI --> Supabase Postgres <-- React dashboard
WooCommerce <--(REST v3)--- FastAPI
```
- FastAPI is the only component that talks to WooCommerce and the email provider.
- React authenticates with Supabase Auth and sends the JWT to FastAPI.
- FastAPI verifies the Supabase JWT on every protected route and uses the service role key server-side only.

## 4. Users and Roles
- **Admin:** full access, manages templates, workflows, and users.
- **Agent:** views and edits customers and orders, adds notes, sends emails.
- Roles are stored in a `profiles` table and enforced in FastAPI dependencies and Supabase RLS.

## 5. Data Model (Supabase / Postgres)
- **profiles**: id (uuid, FK auth.users), full_name, role (`admin|agent`), created_at
- **customers**: id (uuid), woo_customer_id (int, unique, nullable for guests), email (unique), first_name, last_name, phone, billing (jsonb), shipping (jsonb), total_spent, orders_count, tags (text[]), created_at, updated_at, synced_at
- **orders**: id (uuid), woo_order_id (int, unique), customer_id (FK), status, currency, total, payment_method, billing (jsonb), shipping (jsonb), placed_at, updated_at, synced_at
- **order_items**: id, order_id (FK), woo_product_id, name, sku, quantity, price, total
- **order_status_history**: id, order_id, from_status, to_status, changed_at, source (`woo|crm`)
- **customer_notes**: id, customer_id, author_id, body, created_at
- **email_templates**: id, name, trigger_event, subject, body_html (supports `{{variables}}`), is_active
- **communications**: id, customer_id, order_id (nullable), template_id (nullable), channel (`email`), subject, body, status (`queued|sent|failed`), error, sent_at, created_at
- **workflows**: id, name, trigger (`order.created|order.status_changed|customer.created`), conditions (jsonb, e.g. `{"to_status":"completed"}`), template_id, delay_minutes, is_active
- **sync_logs**: id, type (`webhook|full|incremental`), resource, status, details (jsonb), created_at
- **webhook_events**: id, woo_delivery_id (unique), topic, payload (jsonb), processed (bool), created_at

Requirements: indexes on `woo_customer_id`, `woo_order_id`, `customers.email`, `orders.customer_id`, `orders.status`; RLS enabled on all tables; migrations in `/supabase/migrations`.

## 6. WooCommerce Integration
**Auth:** REST API consumer key/secret (Read/Write) via Basic Auth over HTTPS. Config via env vars: `WOO_BASE_URL`, `WOO_CONSUMER_KEY`, `WOO_CONSUMER_SECRET`, `WOO_WEBHOOK_SECRET`.

**Client (`woocommerce_client.py`):**
- Async httpx client with timeouts, retries with exponential backoff, and handling of HTTP 429 and 5xx.
- Methods: `list_customers`, `list_orders`, `get_order`, `update_order_status`. Paginate with `per_page=100` and `page`, reading the `X-WP-TotalPages` header.

**Sync strategy:**
1. **Initial full import:** `POST /sync/full` imports all customers, then orders.
2. **Webhooks:** subscribe to `customer.created`, `customer.updated`, `order.created`, `order.updated`.
3. **Reconciliation:** scheduled job every 15 minutes fetches orders and customers with `modified_after` to catch missed webhooks.
- All writes are **upserts keyed on the Woo ID**, so processing is idempotent.
- Guest orders (customer_id = 0): match or create a customer by billing email.
- Record every sync in `sync_logs`.

**Webhook endpoint:** `POST /webhooks/woocommerce`
- Read the raw body and verify `X-WC-Webhook-Signature` = base64(HMAC-SHA256(raw_body, WOO_WEBHOOK_SECRET)) using constant-time compare. Return 401 on mismatch.
- Deduplicate using `X-WC-Webhook-Delivery-ID` in `webhook_events`.
- Return 200 quickly, then process in a background task.
- When an order status changes, write `order_status_history` and evaluate workflows.

## 7. Backend API (FastAPI, prefix `/api/v1`)
All routes need a valid Supabase JWT except the webhook (signature-verified) and `/health`.

- `GET /health`
- `GET /customers` (search, tag filter, pagination, sort) · `GET /customers/{id}` · `PATCH /customers/{id}` · `POST /customers/{id}/notes` · `GET /customers/{id}/orders` · `GET /customers/{id}/communications`
- `GET /orders` (status, date range, search, pagination) · `GET /orders/{id}` · `PATCH /orders/{id}/status` (updates WooCommerce, then local DB and history)
- `GET|POST|PATCH|DELETE /templates` (admin write)
- `GET|POST|PATCH|DELETE /workflows` (admin write)
- `POST /communications/send` (manual email to a customer, using a template or custom body)
- `GET /communications`
- `GET /dashboard/stats` (revenue, order count, orders by status, new customers, top customers)
- `POST /sync/full` · `GET /sync/status` (admin)
- `POST /webhooks/woocommerce`

Standards: layered code (routers → services → repositories), Pydantic schemas, consistent error format, CORS restricted to the frontend origin, structured logging, and OpenAPI docs at `/docs`.

## 8. Communication Workflows
- A workflow engine evaluates active workflows on each trigger event.
- Template variables: `{{customer.first_name}}`, `{{order.id}}`, `{{order.status}}`, `{{order.total}}`, `{{order.items}}`.
- Flow: event → match workflows → render template → insert `communications` row (`queued`) → send (respecting `delay_minutes`) → update status to `sent` or `failed` with the error.
- Retry failed sends up to 3 times.
- Default seeded templates: Order Confirmation, Order Shipped/Completed, Order Cancelled, Welcome Customer.
- Agents can also send manual emails.

## 9. Frontend (React)
Pages:
1. **Login** (Supabase Auth)
2. **Dashboard:** KPI cards, revenue chart, orders-by-status chart, recent orders
3. **Customers:** searchable and filterable table; **Customer Detail** with profile, orders, notes, tags, and communication history
4. **Orders:** table with status filters; **Order Detail** with items, addresses, status timeline, and a change-status action
5. **Communications:** log and manual compose
6. **Templates and Workflows** (admin): CRUD with live preview
7. **Sync Status** (admin): last sync, webhook failures, "Run full sync" button

Requirements: responsive layout, loading, empty, and error states, optimistic updates where safe, protected routes by role, and TanStack Query for data fetching.

## 10. Non-Functional Requirements
- Secrets only in `.env`; provide `.env.example`.
- Webhook handling returns in under 1 second.
- Idempotent sync with no duplicate customers or orders.
- Input validation on all endpoints; rate limit the public webhook route.
- Never log full customer PII or secrets.

## 11. Implementation Phases
1. **Setup:** repo structure (`/backend`, `/frontend`, `/supabase`), docker-compose, env config, health endpoint, Supabase migrations, and auth wiring.
2. **WooCommerce client and full sync:** client, upsert logic, `POST /sync/full`, and tests with mocked responses.
3. **Webhooks and reconciliation:** signature verification, dedup, background processing, and the scheduled job.
4. **Customers and Orders:** APIs and UI, notes and tags, and status updates pushed to WooCommerce.
5. **Dashboard:** stats endpoint and charts.
6. **Communications:** templates, workflow engine, email provider, and logs.
7. **Hardening and docs:** RLS review, error handling, tests, README with architecture diagram and setup steps, and a demo seed script.

**Definition of done per phase:** code runs locally, tests pass, and the phase's acceptance criteria below are met.

## 12. Acceptance Criteria
- A new order on the WooCommerce test store appears in the CRM within 10 seconds.
- Replaying the same webhook creates no duplicates.
- A webhook with a bad signature is rejected with 401.
- Changing an order status in the CRM updates WooCommerce and records history.
- Completing an order sends the configured email and logs it in `communications`.
- Guest orders are linked to a customer by email.
- Unauthenticated requests to protected routes return 401, and agents cannot access admin routes.

## 13. Testing Plan
- **Unit (pytest):** Woo-to-DB mapping, signature verification, template rendering, and workflow matching.
- **Integration:** mocked WooCommerce (respx) and a test Supabase project, covering the full sync and webhook processing.
- **Webhook simulation:** a script that sends signed payloads, plus duplicate, invalid-signature, and out-of-order cases.
- **Frontend:** component tests for tables and forms, and one Playwright E2E flow (login → open order → change status → verify the email log).
- **Manual:** place a real order on the test store and check the full path.
- **Failure cases:** WooCommerce down, rate limits, and email provider errors.

## 14. Test Store Setup (manual, outside the code)
1. Run WordPress + WooCommerce (Docker, LocalWP, or a free sandbox) and import sample products.
2. Create REST API keys under WooCommerce → Settings → Advanced → REST API.
3. Expose the local FastAPI server with ngrok or cloudflared and register webhooks under WooCommerce → Settings → Advanced → Webhooks, using the webhook secret.
4. Seed fake customers and orders via the API for demos.

## 15. Deliverables
Working app, `docker-compose.yml`, migrations, seed script, `.env.example`, README (architecture, setup, testing), Postman or OpenAPI collection, and demo video.
