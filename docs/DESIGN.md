# Design Spec: WooCommerce CRM

> Instructions for the AI agent: build the React frontend to match this spec. The visual style follows a clean, modern SaaS dashboard: left sidebar, top bar, soft pastel KPI cards, rounded white cards on a light background, and a blue primary color. Use the design tokens below and don't invent new colors. Don't copy any branding from the reference image; use the product name "WooCRM" (placeholder) and a simple logo mark.

## 1. Design Principles
1. **Clarity first:** one clear purpose per card. Numbers big, labels small.
2. **Calm and airy:** generous white space, soft shadows, rounded corners.
3. **Color means something:** blue = primary action, green = success/positive, amber = warning/pending, red = failed/cancelled, purple/teal = categorical accents.
4. **Fast scanning:** KPI cards on top, charts in the middle, lists at the bottom.
5. **Every screen has loading, empty, and error states.**

## 2. Adaptation from the Reference
The reference is a sales-pipeline CRM. Our product is a WooCommerce store CRM, so map the concepts like this:

| Reference element | Our equivalent |
|---|---|
| Total Leads | Total Customers |
| Open Deals | Open Orders (pending, processing, on-hold) |
| Revenue Forecast | Revenue (last 30 days) |
| Conversion Rate | Repeat Customer Rate |
| Sales Pipeline (chevron stages) | Order Pipeline: Pending → Processing → On-hold → Completed (also show Cancelled/Refunded as a muted tail) |
| Deal Activity | Recent Activity (orders, status changes, emails sent, syncs) |
| Team Performance | Top Customers by spend |
| Pipeline Value Over Time | Revenue Over Time |
| Recent Leads | Recent Customers |
| Upcoming Follow-ups | Scheduled / Queued Emails |
| Top Contacts | Recent Orders |
| Sidebar: Leads, Deals, Contacts, Companies, Tasks, Calendar | Customers, Orders, Communications, Templates, Workflows, Sync Status |
| "Upgrade to Pro" card | Sync status mini-card (last synced time, "Sync now" button) |

Not in scope: deals, companies, tasks, calendar, upgrade prompts.

## 3. Design Tokens

### Colors
```
--bg-app:        #F5F7FB   /* page background */
--bg-card:       #FFFFFF
--bg-subtle:     #F0F4FF   /* active nav, hover rows */
--border:        #E6EAF2
--text-primary:  #0F1B3D   /* headings, big numbers */
--text-secondary:#5B6785   /* labels, meta */
--text-muted:    #94A0BD

--primary:       #1D5FE0   /* buttons, active nav, links */
--primary-hover: #174FBD
--primary-soft:  #E5EEFF

--success:       #16A34A   --success-soft: #DCFCE7
--warning:       #F59E0B   --warning-soft: #FEF3C7
--danger:        #DC2626   --danger-soft:  #FEE2E2
--info-teal:     #14B8A6   --teal-soft:    #CCFBF1
--purple:        #8B5CF6   --purple-soft:  #EDE9FE
```

**Order status colors** (badges and pipeline):
| Status | Text | Background |
|---|---|---|
| pending | #B45309 | #FEF3C7 |
| processing | #1D5FE0 | #E5EEFF |
| on-hold | #7C3AED | #EDE9FE |
| completed | #15803D | #DCFCE7 |
| cancelled | #B91C1C | #FEE2E2 |
| refunded | #475569 | #E2E8F0 |
| failed | #B91C1C | #FEE2E2 |

**Pipeline segment colors** (left to right): `#1D5FE0`, `#0EA5E9`, `#2DD4BF`, `#FBBF24`, `#C4B5FD`.

### Typography
- Font: **Inter** (fallback: system-ui, sans-serif).
- Scale: page title 24/32 semibold · card title 16/24 semibold · KPI value 28/36 bold · body 14/20 regular · label/meta 12/16 medium · table header 12 uppercase, tracking-wide.

### Spacing, Radius, Shadow
- Spacing: 4px base (4, 8, 12, 16, 20, 24, 32).
- Card padding: 20px. Gap between cards: 20px. Page padding: 24px.
- Radius: cards 16px · buttons and inputs 10px · badges 999px · icon tiles 12px.
- Shadow: `0 1px 2px rgba(15,27,61,0.04), 0 4px 16px rgba(15,27,61,0.05)`; card border `1px solid var(--border)`.

### Tailwind config sketch
```js
theme: { extend: {
  colors: {
    app: '#F5F7FB', primary: { DEFAULT: '#1D5FE0', hover: '#174FBD', soft: '#E5EEFF' },
    ink: { DEFAULT: '#0F1B3D', 2: '#5B6785', muted: '#94A0BD' },
    line: '#E6EAF2'
  },
  borderRadius: { card: '16px', ctl: '10px' },
  boxShadow: { card: '0 1px 2px rgba(15,27,61,0.04), 0 4px 16px rgba(15,27,61,0.05)' },
  fontFamily: { sans: ['Inter', 'system-ui', 'sans-serif'] }
}}
```

## 4. App Shell

### Layout
```
┌─────────┬──────────────────────────────────────────────┐
│ Sidebar │ Top bar (search · notifications · user menu) │
│ 240px   ├──────────────────────────────────────────────┤
│ fixed   │ Page content (max-width 1440px, scrolls)     │
└─────────┴──────────────────────────────────────────────┘
```

### Sidebar (240px, white, right border)
- Top: logo mark + product name.
- Nav items (icon + label, 40px high, radius 10px): **Dashboard, Customers, Orders, Communications, Templates, Workflows, Sync Status, Settings**.
- Active item: `bg-primary-soft`, `text-primary`, font-medium. Hover: `bg-subtle`.
- Templates, Workflows, Sync Status, and Settings are **admin-only**; hide them for agents.
- Bottom: **Sync card**: "Last synced 2 min ago", a green/red status dot, and a small "Sync now" primary button (admin only).
- Icons: `lucide-react`, 20px, stroke 1.75.
- Mobile (<1024px): sidebar becomes a slide-over drawer opened by a hamburger.

### Top bar (64px, white, bottom border)
- Global search input (pill, `bg-app`, search icon, placeholder "Search customers, orders…"). Debounced 300ms; results dropdown groups Customers and Orders.
- Bell icon with a red count badge (failed emails and sync errors).
- User menu: avatar, name, role label (Admin/Agent), chevron → dropdown with Profile and Sign out.

## 5. Core Components

**KPI card:** icon tile (44px, pastel background, colored icon) on the left; label (12px muted) over a 28px bold value; below, a trend line "▲ 12.4% vs last month" in green (red with ▼ if negative). Shows a skeleton while loading.

**Card:** white, radius 16, shadow-card, 1px border. Header row with title (left) and optional action link "View all" (primary, 12px) or a select (right).

**Button:** primary (filled blue, white text), secondary (white, border), ghost, and danger. Height 40px (32px small). Loading state with a spinner, and disabled at 50% opacity.

**Input / Select / Textarea:** height 40, radius 10, 1px border, focus ring `2px primary/30%` plus primary border. Error state with red border and helper text.

**Badge:** pill, 12px medium, status color pairs from section 3.

**Table:** header row `bg-app`, 12px uppercase muted; rows 56px with hover `bg-subtle`; clickable rows navigate to detail; sticky header; pagination footer (rows per page, prev/next); sortable columns show a chevron.

**Avatar:** circle initials (customers have no photos), 32px, with a pastel background derived from a hash of the name.

**Toast:** top-right, for success, error, and info. Auto-dismiss after 4 seconds.

**Empty state:** centered icon, title, one-line hint, and a primary action if applicable.

**Skeleton:** shimmering rounded blocks matching the final layout.

**Modal / Drawer:** centered modal for confirmations; right-side drawer (480px) for create/edit forms.

## 6. Pages

### 6.1 Login
Centered card (400px) on `bg-app` with the logo, "Sign in" title, email and password fields, a primary button, and an error alert. Optional soft blue blob shapes in the corners.

### 6.2 Dashboard
```
Row 1:  [KPI] [KPI] [KPI] [KPI]            (4 columns)
Row 2:  [ Order Pipeline (2/3) ] [ Recent Activity (1/3) ]
Row 3:  [ Top Customers (1/3) ] [ Revenue Over Time (2/3) ]
Row 4:  [ Recent Customers ] [ Scheduled Emails ] [ Recent Orders ]   (3 columns)
```
- **KPIs:** Total Customers, Open Orders, Revenue (30d), Repeat Customer Rate. Each shows the trend versus the previous 30 days.
- **Order Pipeline:** five chevron-shaped segments (see pipeline colors), each with a stage label, order count, and total value beneath. Footer: "Total Order Value" on the left and the number on the right. Clicking a stage goes to `/orders?status=…`.
- **Recent Activity:** the last 5 events, each with a colored icon tile, a sentence ("Order #1042 moved to Processing"), a source line ("by Woo sync" or the agent's name), and a relative time. "View all" links to Communications.
- **Top Customers:** the top 4–5, each with an avatar, name, a horizontal progress bar (percentage of the top spender), and the amount.
- **Revenue Over Time:** area chart (blue line, gradient fill to transparent), a date range select (7d, 30d, 90d), and a tooltip showing date and amount. Use Recharts.
- **Recent Customers:** initials avatar, name, email or city, and relative time.
- **Scheduled Emails:** date tile (month over day), template name, customer, time, and a status icon.
- **Recent Orders:** avatar, order # and customer, a status badge, and the total.

### 6.3 Customers (list)
- Page header "Customers" with count, search input, tag filter (multi-select), sort select, and an "Export CSV" secondary button.
- Table columns: Customer (avatar + name + email), Phone, Orders, Total Spent, Tags, Last Order, Created.
- Row click opens the detail page.

### 6.4 Customer Detail
```
Header: avatar, name, email, phone, tag chips, [Send email] button
Left (2/3):  Tabs: Orders | Communications | Notes
Right (1/3): Profile card (billing/shipping addresses) · Stats card (orders, total spent, avg order, first/last order)
```
- Notes tab: textarea plus an "Add note" button, with a timeline list below (author, time, body).
- Communications tab: list of emails with a status badge (queued, sent, failed) and an expandable body.
- Editable fields (name, phone, tags) in the profile card via inline edit.

### 6.5 Orders (list)
- Status filter chips along the top (All, Pending, Processing, On-hold, Completed, Cancelled, Refunded) with counts, plus a date range picker and a search input.
- Table columns: Order #, Customer, Status badge, Items, Total, Payment, Placed.

### 6.6 Order Detail
- Header: "Order #1042", a status badge, a **Change status** select/button (confirm modal; shows "Updating WooCommerce…" then a toast), and the placed date.
- Left: items table (name, SKU, qty, price, total) and totals summary.
- Right: Customer card (links to detail), Billing and Shipping address cards, and **Status Timeline** (vertical, dots joined by a line, each with status, source Woo/CRM, and time).
- Below: emails sent for this order.

### 6.7 Communications
- Tabs: **Log** and **Compose**.
- Log: table (Customer, Subject, Template, Status badge, Sent at, Error), filters by status, and a "Retry" action on failed items.
- Compose: customer picker, template select (prefills subject and body), subject input, an HTML/rich text editor, a live preview pane, and a Send button.

### 6.8 Templates (admin)
- List on the left (name, trigger, active toggle); editor on the right with subject, body, a variable helper (click to insert `{{customer.first_name}}`, `{{order.id}}`, `{{order.status}}`, `{{order.total}}`, `{{order.items}}`), and a rendered preview using sample data.

### 6.9 Workflows (admin)
- Cards or table: name, trigger, condition summary ("status → completed"), template, delay, and an active toggle.
- A create/edit drawer with: trigger select, condition builder (to-status select), template select, delay minutes, and active switch.

### 6.10 Sync Status (admin)
- Top card: last sync time, status, and a **Run full sync** button with a progress bar while it runs.
- KPI strip: webhooks received (24h), failed webhooks, records synced, next scheduled reconciliation.
- Table of `sync_logs` (type, resource, status badge, records, time) and a failed webhooks list with an error message.

### 6.11 Settings
- Profile (name), password change, and (admin) user list with a role select.

## 7. Charts
- Library: **Recharts**.
- Area chart: line `#1D5FE0` 2px, gradient fill from `rgba(29,95,224,0.25)` to 0, light grid lines on the y-axis only, 12px muted axis labels, rounded tooltip card with shadow, and the last point highlighted with a dot.
- Progress bars: height 6px, radius 999px, track `#E6EAF2`, fill `primary`.
- Pipeline chevrons: pure CSS or SVG, with `clip-path` arrow shapes, equal widths, and a 4px overlap gap.
- Always provide a text/table fallback via `aria-label` and a visually hidden summary.

## 8. Interaction and State Rules
- Data fetching with TanStack Query: show skeletons on first load and keep previous data during refetch.
- Optimistic UI only for notes and tag edits; order status changes wait for server confirmation.
- Errors: inline error card with a "Retry" button; never a blank screen.
- Destructive actions (delete template or workflow) need a confirm modal.
- Forms: validate on blur and on submit; disable submit while pending.
- Keep filters and pagination in the URL query string.
- Real-time hint: poll the dashboard stats every 60 seconds, or subscribe to Supabase Realtime on `orders` and `communications` to refresh.

## 9. Responsive Behavior
| Breakpoint | Behavior |
|---|---|
| ≥1280px | Full layout as above |
| 1024–1279px | KPI grid 2×2; two-column rows stack to a single column where noted |
| 768–1023px | Sidebar becomes a drawer; tables scroll horizontally |
| <768px | Single column; KPI cards in a 2×2 grid; tables convert to stacked cards for Orders and Customers; the top-bar search collapses to an icon |

## 10. Accessibility
- WCAG AA contrast (primary on white is ≥ 4.5:1; check pastel badges).
- All interactive elements keyboard-reachable with a visible focus ring.
- Icon-only buttons have `aria-label`; the status is never conveyed by color alone (always include text).
- Tables use proper `th` scope; modals trap focus and close on Escape.
- Respect `prefers-reduced-motion` (disable shimmer and chart animations).

## 11. Frontend Structure
```
src/
  app/            router, providers, layout (Sidebar, Topbar)
  components/ui/  Button, Input, Select, Badge, Card, Table, Modal, Drawer, Toast, Skeleton, EmptyState, Avatar
  components/charts/  AreaRevenue, PipelineChevrons, ProgressRow
  features/
    dashboard/ customers/ orders/ communications/ templates/ workflows/ sync/ settings/
  lib/            apiClient, supabase, formatters (currency, date, relative time)
  hooks/          useAuth, useDebounce, useQueryParams
  styles/         tailwind.css (tokens)
```

## 12. Build Order for the UI
1. Tokens, Tailwind config, and base UI components.
2. App shell (sidebar, top bar, routing, auth guard, role-based nav).
3. Dashboard with mock data, then wire to `/dashboard/stats`.
4. Customers list and detail.
5. Orders list and detail with status timeline.
6. Communications (log and compose), Templates, Workflows.
7. Sync Status and Settings.
8. Responsive pass, accessibility pass, and empty/error/loading polish.

## 13. Definition of Done (UI)
- Every page matches the tokens, with no hard-coded hex values outside the config.
- Each data view has loading, empty, and error states.
- Layout holds at 375px, 768px, and 1440px widths.
- Keyboard-only navigation works across the main flows.
- No console errors or warnings.
