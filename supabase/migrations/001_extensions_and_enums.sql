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

