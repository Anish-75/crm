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

