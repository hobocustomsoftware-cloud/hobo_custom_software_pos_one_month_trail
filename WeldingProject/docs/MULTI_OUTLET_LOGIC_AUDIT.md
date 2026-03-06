# Multi-Outlet & Inventory Isolation — Logic Audit

## 1. DATA LEAKAGE TEST

**Requirement:** A user from Outlet A must never see or access Sales or Stock data from Outlet B.

### Fixes applied

| Area | Issue | Fix |
|------|--------|-----|
| **DailySalesSummaryView** | Owner saw all sales; staff saw all their sales across outlets. | Owner: optional `?outlet_id=` filter. Non-owner: filter by `outlet_id=user.primary_outlet_id` and only that outlet's sales. |
| **SalesSummaryReportView** | No outlet filter; Manager could see all branches. | Base queryset passed through `filter_queryset_by_outlet()` before date aggregation. |
| **DashboardAnalyticsView** | Stats, charts, recent activities used unfiltered `SaleTransaction` and `Location`. | `get_stats_by_role`, `get_charts_by_role`, `get_recent_activities` now take `outlet_id`; non-owners use `primary_outlet_id`; sales, pending, cancelled, branch performance, top products and recent sales are all outlet-scoped. |
| **StaffSaleHistoryListView** | Privileged roles saw all sales without outlet filter. | All roles: `filter_queryset_by_outlet(qs)`; non-privileged also filter by `staff=user`. |
| **StaffSalesSummaryView** | Staff saw today's sales across all outlets. | Non-owner: filter by `outlet_id=user.primary_outlet_id`. |
| **ProductListAPIView** | Staff could see stock at locations from other outlets (if assigned). | Non-owner: `assigned_locations` restricted to `outlet_id=primary_outlet_id`; session/primary location must belong to that outlet. |
| **SelectLocationView** | Staff could select any sale location (e.g. another outlet). | Added `user_can_access_location(user, location)`; non-owner can only select locations where `location.outlet_id == user.primary_outlet_id`. |
| **FullInventoryReportView** | Listed all products with no outlet scope. | Non-owner: annotate stock using only movements at `to_location__outlet_id` / `from_location__outlet_id` = user's outlet. |
| **LowStockReportView** | Low-stock count was global across all locations. | Non-owner: same outlet-scoped annotation for `total_in`/`total_out` so low stock is per-outlet only. |
| **Customer InvoiceDetailView** | Any authenticated user could load any approved invoice by ID. | `get_queryset` uses `filter_queryset_by_outlet(SaleTransaction.objects.filter(status='approved'), request)`. |

### Already correct (no change)

- **AdminApprovalView, PendingApprovalListView**: `filter_queryset_by_outlet` on pending sales.
- **InvoiceListView, InvoiceDetailView, InvoicePDFView, InvoiceCancelView**: outlet-scoped via `filter_queryset_by_outlet`.
- **InventoryMovementListView, ExpenseViewSet, TransactionListView**: outlet-scoped.
- **LocationViewSet, LocationListAPIView**: outlet or owner-only.

---

## 2. INVENTORY SYNC TEST

**Requirement:** Inbound to a specific outlet’s warehouse must increase stock only at that outlet and location.

### Verification

- Stock is stored per **location** via `InventoryMovement` (to_location / from_location). There is no single “global” stock field.
- **Inbound:** `InventoryInboundView` and bulk import set `to_location=to_loc` and `outlet_id=to_loc.outlet_id`. `Product.get_stock_by_location(location)` only sums movements for that location, so the increase appears only at that outlet’s warehouse (or whatever `to_loc` is).
- **Outbound:** Sale approval creates movements with `from_location=sale_location` (shopfloor of the sale’s outlet). Deduction is only from that location.
- **Transfer:** Movements record `from_location` and `to_location`; stock is moved between those two locations only.

**Conclusion:** Inbound for an outlet’s warehouse only affects that location’s stock; no cross-outlet or global mix.

---

## 3. OWNER PERMISSIONS

**Requirement:** Only the Owner role can access the Global Dashboard and use the Outlet Filter for all branches.

### Implementation

- **OwnerDashboardView:**  
  - Permission: `IsAdminOrHigher`.  
  - Then: `if not is_owner(request.user): return 403`.  
  - `is_owner(user)` is True for roles whose name (lowercased) is one of: `owner`, `admin`, `super`, `superuser`. So **Owner and Admin** can use the global dashboard and outlet filter.
- **Outlet filter:** `get_request_outlet_id(request)` lets Owner/Admin use `?outlet_id=` or `session['dashboard_outlet_id']`; for non-owners it ignores the param and uses only `user.primary_outlet_id`.

**Strict “Owner only”:** If only the role named “owner” should see the dashboard, change the check to:

```python
if (getattr(request.user, 'role_obj', None) or '').name.lower() != 'owner':
    return Response({"detail": "Owner access required."}, status=403)
```

---

## 4. EDGE CASES

### 4.1 Stock transfer when destination “outlet” doesn’t exist

- **Meaning:** Transfer to a location whose `outlet_id` is missing or whose outlet was deleted.
- **Current behaviour:**  
  - Transfer uses **locations** (e.g. `to_loc_id`, `from_loc_id`).  
  - If `to_loc_id` or `from_loc_id` is invalid: `Location.objects.get(id=...)` raises `Location.DoesNotExist` → caught and **400** with a clear message (“ပစ်မှတ်တည်နေရာကို ရှာမတွေ့ပါ” / “မူရင်းတည်နေရာကို ရှာမတွေ့ပါ”).  
  - If the location exists but `outlet_id` is null or the outlet was deleted: the movement is still created; `user_can_access_location` only allows locations whose `outlet_id` equals the user’s `primary_outlet_id`, so staff cannot target such locations. Owner can; consider adding a check that `to_loc.outlet_id` and `from_loc.outlet_id` exist in `Outlet` if you want to harden further.

### 4.2 Sale request rejected by Manager

- **Current behaviour:**  
  - Rejection only sets `SaleTransaction.status = 'rejected'` (and optional `reject_reason`).  
  - **No stock is deducted on request;** deduction happens only in `AdminApprovalView.perform_update` when `status == 'approved'`.  
  - So when a Manager rejects, there is no inventory change, no reversal, and no reserved stock to release.  
- **Conclusion:** No bug; rejection is a status-only operation.

---

## 5. INBOUND / TRANSFER PERMISSIONS & ERRORS

| Issue | Fix |
|-------|-----|
| Staff could inbound to another outlet’s location | `user_can_access_location(request.user, to_loc)` before creating movement; 403 if not allowed. |
| Staff could transfer from/to another outlet’s locations | Same check for both `from_loc` and `to_loc` in both transfer endpoints; 403 if not allowed. |
| Invalid `to_location` ID in Inbound | `Location.DoesNotExist` caught → 400 “တည်နေရာ ရှာမတွေ့ပါ”. |
| Invalid `from_location` or `to_location` in Transfer | `Location.DoesNotExist` caught → 400 with message for source or destination. |

---

## 6. HELPER ADDED

- **`user_can_access_location(user, location)`** in `core/outlet_utils.py`:  
  - Owner: allowed for any location.  
  - Non-owner: allowed only if `location.outlet_id == user.primary_outlet_id`.  
  Used in: SelectLocationView, InventoryInboundView, both InventoryTransferView handlers.

---

## 7. SUMMARY

- **Data leakage:** Addressed in daily summary, sales summary report, dashboard analytics, staff sale history, staff sales summary, product list, select location, full inventory report, low stock report, and customer invoice detail.
- **Inventory sync:** Confirmed that inbound to an outlet warehouse only affects that location’s stock.
- **Owner permissions:** Global dashboard and outlet filter are restricted to `is_owner` (Owner + Admin); optional strict-owner check documented.
- **Edge cases:** Invalid transfer destination/source return 400; sale rejection has no inventory impact.

All listed fixes are implemented in the codebase.
