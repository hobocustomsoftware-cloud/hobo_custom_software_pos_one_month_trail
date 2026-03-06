# RBAC: Staff Role-Based Access Control

## Assign staff to outlet

- Each staff member (Manager, Cashier, Store Keeper) **must be assigned to one Outlet** via **Primary Outlet**.
- Enforcement: **EmployeeSerializer** (create/update) validates that when role is Manager, Cashier, or Store Keeper, **Primary Outlet** is required.
- On login, all data (Sales, Stock, Reports) is filtered to the user’s **primary_outlet_id** (see `core/outlet_utils.filter_queryset_by_outlet` and view-level filtering).

## Role permissions

| Role        | Access |
|------------|--------|
| **OWNER**  | Full access to all outlets and global reports. No outlet restriction. |
| **MANAGER**| Full access to **assigned outlet only**. Can approve Sale Requests, view reports, invoices, cancel vouchers, dashboard analytics. |
| **CASHIER**| POS only: product list (no cost), create Sale Request, locations (own outlet), staff sale history, staff sales summary, invoice detail/PDF (own outlet). **Cannot**: admin, reports, movements, full invoice list, dashboard analytics, cost prices. |
| **STORE KEEPER** | Inbound, Outbound, Internal Transfers **within assigned outlet only**. **Cannot**: POS (no sale request), admin, reports, approve sales, invoice list. |

## Login security (403 Forbidden)

- **Admin / Reports APIs** use permission **IsManagerOrHigher**.  
  So **Cashier** and **Store Keeper** get **403 Forbidden** when calling:
  - `/api/admin/pending/`, `/api/admin/approve/<id>/`
  - `/api/admin/report/daily-summary/`, `full-inventory/`, `low-stock/`, `sales-period-summary/`
  - `/api/owner-dashboard/`
  - `/api/dashboard/analytics/`
  - `/api/invoices/` (full list), `/api/invoice/<id>/cancel/`
- **Movement APIs** use **IsStoreKeeperOrHigher**.  
  So **Cashier** gets **403** on:
  - `/api/movements/`, `/api/movements/inbound/`, `/api/movements/transfer/`
- **POS APIs** use **IsCashierOrHigher** (staff/items, sales/request, locations, staff history, my-sales-summary, invoice detail/PDF).  
  **Store Keeper** can call these if you want; currently they are allowed (Cashier+ includes any role that can use POS).

If a Cashier opens the frontend at `/app/admin` or `/app/reports`, the **page may load** (SPA), but **all API calls** to the above endpoints return **403**, so no admin or report data is shown.

## Cost hiding for Cashier

- **ProductListSerializer** (POS product list) receives `context['hide_cost'] = True` when the user is **Cashier**.
- In that case, **cost_usd** (and any cost field) is omitted from the response so Cashier cannot see purchase costs.

## Audit log

- **Model:** `core.AuditLog` (user, action, object_type, object_id, outlet, details, created_at).
- **Actions recorded:**
  - **sale_request** – when a Sale Request is created (user = staff).
  - **sale_approve** / **sale_reject** – when a Manager approves or rejects (user = approver).
  - **movement_inbound** – when stock is received (user = moved_by).
  - **movement_transfer** – when stock is transferred (user = moved_by).
  - **invoice_cancel** – when a voucher is cancelled (user = who cancelled).
- Every such action stores **User_ID** (and outlet where applicable) to support audit and reduce internal theft/errors.

## Permission classes (core.permissions)

- **IsManagerOrHigher** – Owner, Admin, Manager (admin & reports).
- **IsCashierOrHigher** – Owner, Admin, Manager, Cashier (POS + sale request).
- **IsStoreKeeperOrHigher** – Owner, Admin, Manager, Store Keeper (+ inventory role) (inbound, outbound, transfer).
- Role names are matched **case-insensitively**; e.g. `store_keeper`, `storekeeper`, `store keeper` and `inventory` are treated as store-keeper–style roles for movements.

## Creating roles

Ensure these roles exist (e.g. in Django Admin or seed data): **owner**, **admin**, **manager**, **cashier**, **store_keeper** (or **storekeeper** / **inventory**). Assign each staff a **Role** and a **Primary Outlet** (except Owner/Admin, who may have no outlet for global access).
