# THE MASTER BLUEPRINT: Cloud-Based Myanmar Universal POS (AI-Powered)

## 1. Hosting & Domain Architecture

| Requirement | Description |
|------------|-------------|
| **Multi-Tenancy** | Subdomain-based access (e.g. `shoppy.yourpos.com`). Each tenant gets a subdomain or path for their POS. |
| **License System** | License key validation on first login/setup. Trial, grace, and licensed states; remaining days surfaced in UI. |
| **Online/Offline** | Local Storage (and/or IndexedDB) buffers sales data when internet is down; auto-sync when back online. |

---

## 2. Advanced AI & Reporting (Owner Dashboard)

| Area | Description |
|------|-------------|
| **AI Recommendations** | Insights on: low-stock prediction from sales velocity; P&amp;L trends by industry mode; top-selling and slow-moving items. |
| **Remote Monitoring** | Owners can view real-time sales and stock levels from any device via their domain. |

---

## 3. Universal Industry Features (Loyverse Simple UI)

| Item | Description |
|------|-------------|
| **Settings Toggle** | [Pharmacy, Solar, Hardware, Phone, General] — industry mode drives which features are active. |
| **Features** | 3-Level Units (လုံး/ကဒ်/ဗူး), Serial/IMEI Tracking, Site Survey, Flexible Bundling. |
| **UI Standard** | 25px Myanmar text, 80px buttons, Loyverse 70/30 layout. |

---

## 4. Hardware Integration (Cloud-to-Local)

| Item | Description |
|------|-------------|
| **Printing** | Optimized 58mm/80mm Myanmar printing for web-to-thermal bridge (iframe print + optional Capacitor Bluetooth). |
| **Scanning** | Global USB barcode/QR listener integrated in the browser/app (keyboard-wedge + camera scan). |

---

## 5. Simplified Fast Payment

| Item | Description |
|------|-------------|
| **Modes** | [Cash / ငွေသား, KPay, WavePay, AYAPay, Card, Credit / အကြွေး]. |
| **Flow** | Instant checkout without mandatory Transaction ID for maximum speed. |

---

## Implementation Map

| Blueprint Section | Current Implementation |
|-------------------|------------------------|
| **1. Hosting & Domain** | License activation/validation; offline POS store with sync; multi-tenant via subdomain (deploy/config). |
| **2. AI & Reporting** | AI cross-sell/tips; exchange-rate; reports (Sales, P&amp;L, Inventory); stock prediction; dashboard analytics. Extend with remote monitoring. |
| **3. Industry Features** | Business type: Phone, Pharmacy, Hardware, **Solar/Air-con**, General. Serial/Unit modals; 25px/80px/70-30. Site Survey (solar_aircon) ready for extension. |
| **4. Hardware** | `usePrintReceipt` (58/80mm, Myanmar font); `useBarcodeListener` (USB wedge); Docker USB snippet; BarcodeScanner (camera). |
| **5. Fast Payment** | Modes: Cash/ငွေသား, KPay, WavePay, AYAPay, Card/MPU, **Credit/အကြွေး**. 80px buttons; click = complete sale (no Transaction ID); payment method recorded. |

---

## API & Frontend Verification

See **`yp_posf/docs/API_INTEGRATION_VERIFICATION.md`** for a full list of frontend API calls and backend routes. All endpoints are wired and compatible (အဆင်ပြေ).

For **Multi-Device** (PC, Tablet, Phone), **Responsive UI**, **Cross-Device Hardware**, and **License on any device**, see **`FINAL_MASTER_BLUEPRINT.md`**.
