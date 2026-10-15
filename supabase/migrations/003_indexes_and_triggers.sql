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

