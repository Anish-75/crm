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

