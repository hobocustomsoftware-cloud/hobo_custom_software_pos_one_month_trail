# HoBo POS – UI Design System (ဒီ System နဲ့ ကိုက်ညီတဲ့ Design)

ဒီ document က **HoBo POS** စနစ်နဲ့ ကိုက်ညီတဲ့ UI design ကို သတ်မှတ်ထားပါတယ်။ ဘယ် device ကနေပဲ ကြည့်ကြည့် layout အချိုးညီပြီး responsive ဖြစ်အောင် ပြင်ထားပါတယ်။

---

## ၁။ Brand & Theme

| အရာ | သတ်မှတ်ချက် |
|------|----------------|
| **Primary** | `#aa0000` (Deep Red) – ပစ္စည်းအရောင်း / POS စနစ် |
| **Background** | `#151515` (Dark Charcoal) |
| **Accent** | ဖြူ/ငွေရောင် (text, border) |
| **Font** | Inter (Sans-serif) |
| **Style** | Apple-style Glassmorphism (ဖန်တီးမှု ပြောင်းလဲမှု) |

---

## ၂။ Layout ဖွဲ့စည်းပုံ

### ၂.၁ Sidebar (ဘယ်ဘက်)
- **Desktop (lg နဲ့ အထက်):** **Icon-only** – အကျယ် `4.5rem` (72px)၊ icon တွေပဲြပြီး နာမည်စာသား မပြ။
- **Mobile/Tablet:** Drawer – ဖွင့်မှ icon + နာမည် ပြမယ်၊ အကျယ် `18rem` (288px) / မျက်နှာပြင် ၈၅%။
- Icon ပေါ်မှာ **hover လုပ်ရင် browser tooltip** (title) နဲ့ ဘာလဲ ပြမယ်။
- Active link ကို `bg-white/20` + အနည်းငယ် glow နဲ့ ခွဲပြမယ်။

### ၂.၂ Main Content (ဘေးက content)
- **Container:** `.layout-container` – `max-width: 1400px`, ဘေးဘက် padding responsive:
  - Mobile: `1rem`
  - sm: `1.5rem`
  - lg: `2rem`
- **Main area:** Sidebar ဘေးမှာ `flex-1` နဲ့ ကျယ်ကျယ် ယူပြီး၊ အတွင်းမှာ `layout-container` သုံးလို့ စာမျက်နှာတိုင်း အချိုးညီအောင် ထားပါတယ်။
- **Responsive:** မျက်နှာပြင်သေးရင် content က ဒီ container အတွင်းမှာပဲ ကျဉ်းပြီး ပြ၊ ကြီးရင် ဗဟိုချက်ညီအောင် ထားပါတယ်။

### ၂.၃ Topbar
- အမြင့် သတ်မှတ် (ဥပမာ `h-14` / `sm:h-20`) နဲ့ glass effect သုံးပြီး notification, user menu ထားပါတယ်။
- Mobile မှာ sidebar ဖွင့်ခလုတ် ပြမယ်။

---

## ၃။ Components သတ်မှတ်ချက်များ

| Component | သတ်မှတ်ချက် |
|-----------|----------------|
| **Card** | `.glass-card` – semi-transparent, blur, အနားသတ် ပါးပါး |
| **Input** | `.glass-input` – focus မှာ primary အနည်းငယ် glow |
| **Label** | `.glass-label` – မှိန်းတဲ့ စာရောင် |
| **Primary Button** | `.btn-primary` – Deep Red gradient + hover မှာ glow |
| **Secondary Button** | `.btn-secondary` – Ghost/Outline style |

---

## ၄။ Responsive Breakpoints (Tailwind နဲ့ ကိုက်ညီ)

- **Default:** Mobile-first (သေးငယ်တဲ့ စခရင်)
- **sm:** 640px – ဖုန်းအကြီး / ထောင့်ဖြတ်
- **md:** 768px – Tablet
- **lg:** 1024px – Sidebar က **icon-only** ဖြစ်ပြီး content နေရာ ပိုရမယ်
- **xl:** 1280px – Desktop ကြီး
- **2xl:** 1536px – မျက်နှာပြင်ကြီး

ဘယ် device ကနေပဲ ကြည့်ကြည့်:
- Sidebar က ဒီ breakpoints အတိုင်း (mobile = drawer, desktop = icon-only) ပြောင်းမယ်။
- Content က `.layout-container` ကြောင့် အချိုးညီပြီး ဗဟိုချက်ညီမယ်။

---

## ၅။ ဒီ System နဲ့ ကိုက်ညီအောင် လုပ်ထားတာများ

1. **Sidebar** – Desktop မှာ icon-only၊ mobile မှာ full menu + drawer။
2. **Main layout** – `MainLayout.vue` မှာ `layout-container` နဲ့ padding responsive သတ်မှတ်ပြီး။
3. **Dashboard** – Bento-style grid၊ glass cards၊ responsive columns (1 → 2 → 4 columns)။
4. **Login / Register** – glass card နဲ့ တစ်စီတစ်ညီ။
5. **Safe area** – Mobile notch / home indicator အတွက် padding သတ်မှတ်ပြီး။

---

## ၆။ နောက်ထပ် လုပ်ချင်ရင်

- List/table စာမျက်နှာတွေမှာ **paginator** + **filter/search** ထည့်ပြီး layout ကို `.layout-container` အတွင်းမှာပဲ ထားပါ။
- Form စာမျက်နှာတွေမှာ `glass-input` / `glass-label` / `btn-primary` သုံးပြီး theme ကို တစ်စီတစ်ညီ ထားပါ။
- Modal/Dialog တွေမှာ glass card + backdrop blur သုံးပါ။

ဒီသတ်မှတ်ချက်အတိုင်း ပြင်ထားလို့ **HoBo POS** စနစ်နဲ့ ကိုက်ညီတဲ့ design ဖြစ်ပြီး၊ **responsive** နဲ့ **layout အချိုးညီ** အောင် ထားပါတယ်။
