# Database Design: WooCommerce CRM (Supabase / Postgres)

> Instructions for the AI agent: put the SQL below into ordered migration files under `/supabase/migrations`. Keep the names and constraints exactly as written unless told otherwise. Never expose the service role key to the frontend.

## 1. Overview
- Database: Supabase Postgres 15+
- Auth: Supabase Auth (`auth.users`), extended by `profiles`
- Primary keys: `uuid` (default `gen_random_uuid()`)
- Woo IDs are stored as `woo_*_id` integers with unique constraints, so all syncing is an **upsert on the Woo ID**.
- Timestamps are `timestamptz`, default `now()`.

## 2. Entity Relationships
```
auth.users 1─1 profiles
customers  1─N orders 1─N order_items
orders     1─N order_status_history
customers  1─N customer_notes (author → profiles)
customers  1─N communications (optional order, optional template)
email_templates 1─N workflows
```

## 3. Migration 001: Extensions, Enums, Helpers
```sql
create extension if not exists "pgcrypto";
create extension if not exists "pg_trgm";

create type user_role as enum ('admin', 'agent');
create type comm_status as enum ('queued', 'sent', 'failed');
create type comm_channel as enum ('email');
create type status_source as enum ('woo', 'crm');
create type sync_type as enum ('webhook', 'full', 'incremental');
create type sync_status as enum ('success', 'partial', 'failed');
create type workflow_trigger as enum (
  'order.created', 'order.status_changed', 'customer.created'
);

create or replace function set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end $$;
```

## 4. Migration 002: Tables
```sql
-- Users
create table profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  full_name text,
  role user_role not null default 'agent',
  created_at timestamptz not null default now()
);

-- Customers
create table customers (
  id uuid primary key default gen_random_uuid(),
  woo_customer_id integer unique,            -- null for guest customers
  email text not null unique,
  first_name text,
  last_name text,
  phone text,
  billing jsonb not null default '{}'::jsonb,
  shipping jsonb not null default '{}'::jsonb,
  total_spent numeric(12,2) not null default 0,
  orders_count integer not null default 0,
  tags text[] not null default '{}',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  synced_at timestamptz
);

-- Orders
create table orders (
  id uuid primary key default gen_random_uuid(),
  woo_order_id integer not null unique,
  customer_id uuid references customers(id) on delete set null,
  status text not null,                       -- Woo statuses: pending, processing, on-hold, completed, cancelled, refunded, failed
  currency text not null default 'USD',
  total numeric(12,2) not null default 0,
  payment_method text,
  billing jsonb not null default '{}'::jsonb,
  shipping jsonb not null default '{}'::jsonb,
  placed_at timestamptz not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  synced_at timestamptz
);

create table order_items (
  id uuid primary key default gen_random_uuid(),
  order_id uuid not null references orders(id) on delete cascade,
  woo_product_id integer,
  name text not null,
  sku text,
  quantity integer not null check (quantity > 0),
  price numeric(12,2) not null,
  total numeric(12,2) not null
);

create table order_status_history (
  id uuid primary key default gen_random_uuid(),
  order_id uuid not null references orders(id) on delete cascade,
  from_status text,
  to_status text not null,
  source status_source not null default 'woo',
  changed_by uuid references profiles(id) on delete set null,
  changed_at timestamptz not null default now()
);

-- Notes
create table customer_notes (
  id uuid primary key default gen_random_uuid(),
  customer_id uuid not null references customers(id) on delete cascade,
  author_id uuid references profiles(id) on delete set null,
  body text not null,
  created_at timestamptz not null default now()
);

-- Communications
create table email_templates (
  id uuid primary key default gen_random_uuid(),
  name text not null unique,
  trigger_event workflow_trigger,
  subject text not null,
  body_html text not null,                    -- supports {{customer.first_name}}, {{order.id}}, etc.
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table workflows (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  trigger workflow_trigger not null,
  conditions jsonb not null default '{}'::jsonb,  -- e.g. {"to_status":"completed"}
  template_id uuid not null references email_templates(id) on delete restrict,
  delay_minutes integer not null default 0 check (delay_minutes >= 0),
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table communications (
  id uuid primary key default gen_random_uuid(),
  customer_id uuid not null references customers(id) on delete cascade,
  order_id uuid references orders(id) on delete set null,
  template_id uuid references email_templates(id) on delete set null,
  workflow_id uuid references workflows(id) on delete set null,
  sent_by uuid references profiles(id) on delete set null,  -- null = automated
  channel comm_channel not null default 'email',
  subject text not null,
  body text not null,
  status comm_status not null default 'queued',
  attempts integer not null default 0,
  error text,
  scheduled_for timestamptz not null default now(),
  sent_at timestamptz,
  created_at timestamptz not null default now()
);

-- Sync and webhooks
create table sync_logs (
  id uuid primary key default gen_random_uuid(),
  type sync_type not null,
  resource text not null,                     -- 'customers' | 'orders'
  status sync_status not null,
  records_processed integer not null default 0,
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table webhook_events (
  id uuid primary key default gen_random_uuid(),
  woo_delivery_id text not null unique,       -- X-WC-Webhook-Delivery-ID, used for dedup
  topic text not null,
  payload jsonb not null,
  processed boolean not null default false,
  error text,
  created_at timestamptz not null default now(),
  processed_at timestamptz
);
```

## 5. Migration 003: Indexes and Triggers
```sql
create index idx_customers_name_trgm on customers
  using gin ((coalesce(first_name,'') || ' ' || coalesce(last_name,'') || ' ' || email) gin_trgm_ops);
create index idx_customers_tags on customers using gin (tags);

create index idx_orders_customer on orders(customer_id);
create index idx_orders_status on orders(status);
create index idx_orders_placed_at on orders(placed_at desc);

create index idx_order_items_order on order_items(order_id);
create index idx_status_history_order on order_status_history(order_id, changed_at desc);
create index idx_notes_customer on customer_notes(customer_id, created_at desc);

create index idx_comm_customer on communications(customer_id, created_at desc);
create index idx_comm_order on communications(order_id);
create index idx_comm_queue on communications(status, scheduled_for) where status = 'queued';

create index idx_workflows_trigger on workflows(trigger) where is_active;
create index idx_webhook_unprocessed on webhook_events(created_at) where processed = false;
create index idx_sync_logs_created on sync_logs(created_at desc);

create trigger trg_customers_updated before update on customers
  for each row execute function set_updated_at();
create trigger trg_orders_updated before update on orders
  for each row execute function set_updated_at();
create trigger trg_templates_updated before update on email_templates
  for each row execute function set_updated_at();
create trigger trg_workflows_updated before update on workflows
  for each row execute function set_updated_at();
```

## 6. Migration 004: Auth Profile Trigger
Creates a `profiles` row for each new Supabase user. Promote the first admin manually.
```sql
create or replace function handle_new_user()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  insert into profiles (id, full_name)
  values (new.id, new.raw_user_meta_data->>'full_name');
  return new;
end $$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function handle_new_user();

-- Promote an admin (run once manually):
-- update profiles set role = 'admin' where id = '<user-uuid>';
```

## 7. Migration 005: Row Level Security
The FastAPI backend uses the **service role key**, which bypasses RLS. RLS protects any direct access from the browser with the anon key.

```sql
create or replace function is_admin()
returns boolean language sql stable security definer set search_path = public as $$
  select exists (select 1 from profiles where id = auth.uid() and role = 'admin');
$$;

create or replace function is_staff()
returns boolean language sql stable security definer set search_path = public as $$
  select exists (select 1 from profiles where id = auth.uid());
$$;

alter table profiles             enable row level security;
alter table customers            enable row level security;
alter table orders               enable row level security;
alter table order_items          enable row level security;
alter table order_status_history enable row level security;
alter table customer_notes       enable row level security;
alter table email_templates      enable row level security;
alter table workflows            enable row level security;
alter table communications       enable row level security;
alter table sync_logs            enable row level security;
alter table webhook_events       enable row level security;

-- Profiles: read own row, admins read all
create policy "profiles_select" on profiles for select
  using (id = auth.uid() or is_admin());

-- Staff read access to CRM data
create policy "customers_read"  on customers  for select using (is_staff());
create policy "orders_read"     on orders     for select using (is_staff());
create policy "items_read"      on order_items for select using (is_staff());
create policy "history_read"    on order_status_history for select using (is_staff());
create policy "comms_read"      on communications for select using (is_staff());
create policy "templates_read"  on email_templates for select using (is_staff());
create policy "workflows_read"  on workflows for select using (is_staff());

-- Staff can edit customer details and manage their own notes
create policy "customers_update" on customers for update
  using (is_staff()) with check (is_staff());
create policy "notes_read"   on customer_notes for select using (is_staff());
create policy "notes_insert" on customer_notes for insert
  with check (is_staff() and author_id = auth.uid());
create policy "notes_delete" on customer_notes for delete
  using (author_id = auth.uid() or is_admin());

-- Admin-only management
create policy "templates_admin" on email_templates for all
  using (is_admin()) with check (is_admin());
create policy "workflows_admin" on workflows for all
  using (is_admin()) with check (is_admin());
create policy "sync_logs_admin" on sync_logs for select using (is_admin());

-- webhook_events: no policies, so only the service role can access it
```

## 8. Migration 006: Seed Data
```sql
insert into email_templates (name, trigger_event, subject, body_html) values
('Order Confirmation', 'order.created',
 'We received your order #{{order.id}}',
 '<p>Hi {{customer.first_name}},</p><p>Thanks for your order #{{order.id}} totalling {{order.total}}.</p>{{order.items}}'),
('Order Completed', 'order.status_changed',
 'Your order #{{order.id}} is complete',
 '<p>Hi {{customer.first_name}},</p><p>Your order #{{order.id}} has been completed.</p>'),
('Order Cancelled', 'order.status_changed',
 'Your order #{{order.id}} was cancelled',
 '<p>Hi {{customer.first_name}},</p><p>Your order #{{order.id}} has been cancelled.</p>'),
('Welcome', 'customer.created',
 'Welcome, {{customer.first_name}}!',
 '<p>Hi {{customer.first_name}}, thanks for joining us.</p>');

insert into workflows (name, trigger, conditions, template_id)
select 'Send order confirmation', 'order.created', '{}'::jsonb, id
  from email_templates where name = 'Order Confirmation';

insert into workflows (name, trigger, conditions, template_id)
select 'Notify on completed', 'order.status_changed', '{"to_status":"completed"}'::jsonb, id
  from email_templates where name = 'Order Completed';

insert into workflows (name, trigger, conditions, template_id)
select 'Notify on cancelled', 'order.status_changed', '{"to_status":"cancelled"}'::jsonb, id
  from email_templates where name = 'Order Cancelled';

insert into workflows (name, trigger, conditions, template_id)
select 'Welcome new customers', 'customer.created', '{}'::jsonb, id
  from email_templates where name = 'Welcome';
```

## 9. Key Queries and Patterns

**Upsert customer from Woo** (repository layer):
```sql
insert into customers (woo_customer_id, email, first_name, last_name, phone, billing, shipping, synced_at)
values ($1, $2, $3, $4, $5, $6, $7, now())
on conflict (email) do update set
  woo_customer_id = coalesce(excluded.woo_customer_id, customers.woo_customer_id),
  first_name = excluded.first_name,
  last_name = excluded.last_name,
  phone = excluded.phone,
  billing = excluded.billing,
  shipping = excluded.shipping,
  synced_at = now()
returning id;
```

**Upsert order:** `insert ... on conflict (woo_order_id) do update set ...`. For items, delete and reinsert inside the same transaction, or upsert on `(order_id, woo_product_id)`.

**Record a status change only when it differs:** compare `orders.status` to the incoming status before inserting into `order_status_history`.

**Refresh customer totals after an order upsert:**
```sql
update customers c set
  orders_count = s.cnt,
  total_spent  = s.total
from (
  select customer_id, count(*) cnt, coalesce(sum(total), 0) total
  from orders
  where customer_id = $1 and status not in ('cancelled','failed','refunded')
  group by customer_id
) s
where c.id = s.customer_id;
```

**Dashboard stats:**
```sql
-- Orders by status
select status, count(*) from orders group by status;

-- Revenue per day (last 30 days)
select date_trunc('day', placed_at) d, sum(total)
from orders
where placed_at > now() - interval '30 days'
  and status not in ('cancelled','failed','refunded')
group by 1 order by 1;

-- Top customers
select id, email, total_spent from customers order by total_spent desc limit 5;
```

**Email queue worker:** select `communications` where `status = 'queued' and scheduled_for <= now()`, using `for update skip locked` to avoid double sends. Mark `sent` or increment `attempts`, and mark `failed` after 3 attempts.

## 10. Rules for the Agent
- Never delete rows from `webhook_events` or `sync_logs` manually; use a retention job (for example, 90 days).
- Always dedupe webhooks through `webhook_events.woo_delivery_id` before processing.
- All sync writes must be idempotent upserts.
- Keep money as `numeric(12,2)`, never float.
- Add new schema changes as new numbered migrations; don't edit old ones.
- Store only the PII needed for CRM use, and never log full customer records.
