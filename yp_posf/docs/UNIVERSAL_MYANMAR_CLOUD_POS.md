# EXECUTE: Universal Myanmar Cloud POS

## 1. Industry Engine (Smart Toggle System)

### Settings dropdown
- **[Pharmacy]** → `pharmacy_clinic`
- **[Solar/AC]** → `solar_aircon`
- **[Phone/PC]** → `phone_electronics`
- **[Hardware]** → `hardware_store`
- **[General]** → `general_retail`

### Dynamic UI logic

| Mode | Enable | Hide |
|------|--------|------|
| **Pharmacy** | 3-level Units (လုံး/ကဒ်/ဗူး) + Expiry | Serial |
| **Solar/AC** | Bundle Editor + Site Survey Module + Serial Tracking | — |
| **Phone/PC** | Serial (IMEI) Tracking | Multi-Units |
| **Hardware** | Dozen/Bulk Units (ခု/ဒါဇင်/ဖာ) + Credit (အကြွေး) Payment | — |
| **General** | Default (no serial, no multi-unit) | — |

---

## 2. Loyverse-Style & Senior-Friendly UI (25px)

| Rule | Implementation |
|------|----------------|
| **Layout** | 70/30 Split — **Left: Cart**, **Right: Product Grid**. Responsive: mobile = tabbed (ပစ္စည်း \| စာရင်း). |
| **Typography** | Global **25px** Noto Sans Myanmar (`.pos-text`, `.pos-btn`, inputs). |
| **Controls** | All buttons and inputs **80px height** (`.pos-btn`, `.a11y-select`, min-h-[80px]). |
| **Responsive** | Tailwind grid: 1 col mobile, 70/30 from `lg` (1024px). |

---

## 3. Advanced Inventory & Sales Logic

| Feature | Implementation |
|---------|----------------|
| **Multi-Unit Matrix** | Pharmacy: Piece → Strip → Box (လုံး/ကဒ်/ဗူး). Hardware: Piece → Dozen → Bulk (ခု/ဒါဇင်/ဖာ). Auto-conversion and stock deduction via `UnitSelectorModal` + backend. |
| **Flexible Bundling** | Bundle Editor for Solar/AC; swap components in a set; real-time price updates in cart (bundle configurator + API). |
| **Fast Payment** | Buttons: [Cash, KPay, Wave, AYA, Card, Credit]. Instant checkout — **no Transaction ID** required. |

---

## 4. Cloud, AI & License Security

| Item | Implementation |
|------|----------------|
| **License System** | License Key activation check on **first boot** (App.vue: `license/status` when token exists). 403 `license_expired` → redirect to License Activation. |
| **Remote Dashboard** | Sales/P&amp;L synced to host; owner can view live sales and reports from any device (same domain/API). |
| **AI Insights** | Low Stock Predictions (`ai/stock-prediction`); Profit Trends (P&amp;L, dashboard analytics); notification/banner for alerts. |

---

## 5. Hardware & Localization

| Item | Implementation |
|------|----------------|
| **Printing** | 58mm/80mm thermal receipt; Myanmar Unicode (Noto Sans Myanmar in receipt HTML). Web iframe print; Capacitor/Bluetooth stub for mobile. |
| **Scanner** | Global barcode listener (USB/Bluetooth keyboard wedge); camera scan (BarcodeScanner) on mobile. |
| **Cleanup** | No complex animations in POS (`.pos-layout`); high-contrast, professional look; simple transitions only. |

---

## Implementation checklist

- [x] Industry dropdown: Pharmacy, Solar/AC, Phone/PC, Hardware, General
- [x] Pharmacy: 3-level units + expiry; serial hidden
- [x] Solar/AC: Serial + Site Survey + Bundle (getters; Bundle UI per feature)
- [x] Phone/PC: Serial only; multi-unit hidden
- [x] Hardware: Dozen/Bulk unit selector + Credit payment button
- [x] 70/30 layout (left cart, right grid); 25px; 80px controls
- [x] Responsive grid + mobile tabbed POS
- [x] Fast payment buttons; instant checkout
- [x] License check on app load
- [x] 58/80mm Myanmar receipt; global barcode listener
- [x] POS cleanup: minimal transitions, high-contrast
