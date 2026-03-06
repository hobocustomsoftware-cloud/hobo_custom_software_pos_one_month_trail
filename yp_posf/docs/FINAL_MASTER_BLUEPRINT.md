# FINAL MASTER BLUEPRINT: Multi-Device AI Cloud POS

## 1. Responsive UI Architecture (PC, Tablet, Phone)

| Device | Layout | Notes |
|--------|--------|--------|
| **Desktop/Tablet** | Standard Loyverse **70/30 Split** (Products 70%, Cart 30%). | Single view; Tailwind responsive grid. |
| **Mobile** | **Stacked/Tabbed UI**: one tab for Product Grid, one tab for Cart. | Preserves 25px font and 80px buttons; no squashing. |
| **Framework** | Responsive grid (Tailwind) that adapts to all screen sizes. | Breakpoint: mobile tabs below `lg` (1024px), 70/30 above. |

---

## 2. Cross-Device Hardware Support

| Platform | Printing | Scanning |
|----------|----------|----------|
| **PC** | USB thermal printers via browser print (hidden iframe 58mm/80mm) or backend USB mapping (Docker). | Keyboard-emulated (USB) barcode scanners — global keydown listener, buffer + Enter. |
| **Mobile/Tablet** | Camera-based scanning (BarcodeScanner component). | Bluetooth printer support via **Capacitor** or **Web Bluetooth API** (stub: `window.CapacitorPrint.print(html)`). |

---

## 3. Cloud-Based Remote Management

| Requirement | Implementation |
|-------------|-----------------|
| **Centralized Database** | All devices (PC in shop, phone in owner’s pocket) sync to the **same Hosting/Domain** via REST API. Offline: Local Storage / IndexedDB buffers sales; auto-sync when online. |
| **Real-time Dashboard** | Owner can view **live sales**, **AI insights**, and **P&amp;L reports** from any device via their unique subdomain (multi-tenant ready). |

---

## 4. All-In-One Industry Features (Reminder)

| Area | Details |
|------|--------|
| **Settings** | [Pharmacy, Solar, Hardware, Phone, General] — industry mode drives features. |
| **Logic** | Serial/IMEI tracking; 3-Level Units (လုံး/ကဒ်/ဗူး); Dozen/Bulk; Site Survey (Solar/Air-con). |
| **Payment** | Fast Mobile Pay (No Transaction ID required) + Cash, KPay, WavePay, AYAPay, Card, **Credit/အကြွေး**. |

---

## 5. Security & Licensing

| Requirement | Implementation |
|-------------|-----------------|
| **License Activation** | Software checks for a **valid License Key** regardless of the device (PC, tablet, phone). API returns 403 `license_expired` → redirect to License Activation; optional **license/status** check on app load when user is logged in. |

---

## Implementation Summary

| Section | Status |
|---------|--------|
| **§1 Responsive** | 70/30 on desktop/tablet (`lg:` breakpoint); mobile tabbed POS (ပစ္စည်း / စာရင်း) with 25px/80px in `SalesRequest.vue`. |
| **§2 Hardware** | PC: iframe print + USB barcode listener; Mobile: BarcodeScanner + Capacitor/Bluetooth print stub in `usePrintReceipt.js`. |
| **§3 Cloud** | Single API host; offline queue + sync; dashboard and reports for remote monitoring. |
| **§4 Industry** | Business type + Serial/Unit/Site Survey; fast payment with Credit (Settings + SalesRequest). |
| **§5 License** | License validation on API (403 → redirect); **license/status** check on app load in `App.vue` for any device. |
