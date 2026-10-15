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

