# one_month_trial – Demo မှာ ဆိုင်တစ်ဆိုင် / ဆိုင်သုံးလေးငါးဆိုင် / ဆိုင်ချုပ် ၂၀×ခွဲ ၄–၈ စမ်းနည်း

## ပြဿနာ

ဆိုင်တစ်ဆိုင်ဖွင့်ကြည့်ပြီး နောက်ဆိုင်တွေ ထပ်ဖွင့်ကြည့်လို့ မရဖြစ်နေရင် အောက်က အဆင့်တွေ စစ်ပါ။

---

## ၁။ ဆိုင်အရေအတွက် ဖန်တီးခြင်း (Script ပြေးရမယ်)

### ပုံမှန် (ဆိုင်ချုပ် ၁ + ဆိုင်ခွဲ ပြား)

**အကြောင်းရင်း:** လက်ရှိ database မှာ ဆိုင်တစ်ဆိုင်ပဲ (MAIN) ရှိရင် နောက်ဆိုင်တွေ မရှိတော့ “ထပ်ဖွင့်လို့မရ” ဖြစ်တတ်ပါတယ်။

**လုပ်ရမည်:** Management command ကို **ဆိုင်အရေအတွက်** ပေးပြီး ပြေးပါ။

```bash
cd one_month_trial/WeldingProject

# တစ်ဆိုင်တည်း (ဆိုင်ချုပ် MAIN ပဲ) – လက်ရှိလို
python manage.py reset_trial_20_outlets --flush --outlets 1

# ဆိုင်သုံးဆိုင် (ဆိုင်ချုပ် + ဆိုင်ခွဲ ၂) – Demo အတွက် သုံးလေးငါးဆိုင် စမ်းချင်ရင်
python manage.py reset_trial_20_outlets --flush --outlets 3

# ဆိုင်ငါးဆိုင်
python manage.py reset_trial_20_outlets --flush --outlets 5
```

- `--flush` = database ရှင်းပြီး migrate + base units ပြန်ထည့်မယ်။  
- `--outlets 3` = ဆိုင်ချုပ် (MAIN) ၁ + ဆိုင်ခွဲ (BRANCH_01, BRANCH_02) ၂ = စုစုပေါင်း ၃ ဆိုင် ဖန်တီးမယ်။  

### ဆိုင်ချုပ် ၂၀ + တစ်ချုပ်၌ ဆိုင်ခွဲ ၄–၈ ဆိုင်

ဆိုင်က ၂၀ လောက်ရှိမယ်၊ အဲမှာ ဆိုင်ခွဲတွေက အနည်းဆုံး ၄–၈ ဆိုင် စီ ရှိမယ်ဆိုရင် ဒီလို သုံးပါ။  

```bash
# ဆိုင်ချုပ် ၂၀ + တစ်ချုပ်၌ ခွဲ ၆ ဆိုင် (စုစုပေါင်း ၂၀ + ၁၂၀ = ၁၄၀ ဆိုင်)
python manage.py reset_trial_20_outlets --flush --outlets 20 --branches-per-main 6

# ခွဲ ၄ ဆိုင် သာ တစ်ချုပ်၌ (၂၀ + ၈၀ = ၁၀၀ ဆိုင်)
python manage.py reset_trial_20_outlets --flush --outlets 20 --branches-per-main 4

# ခွဲ ၈ ဆိုင် တစ်ချုပ်၌ (၂၀ + ၁၆၀ = ၁၈၀ ဆိုင်)
python manage.py reset_trial_20_outlets --flush --outlets 20 --branches-per-main 8
```

- `--outlets 20` = ဆိုင်ချုပ် (top-level) ၂၀ ဖန်တီးမယ် (MAIN_01 … MAIN_20)။  
- `--branches-per-main 6` = ဆိုင်ချုပ် တစ်ချုပ်၌ ဆိုင်ခွဲ ၆ ဆိုင် စီ ဖန်တီးမယ်။  
- Model မှာ `parent_outlet` ထည့်ထားပြီး ဆိုင်ခွဲတွေက သက်ဆိုင်ရာ ဆိုင်ချုပ် အောက်မှာ ရှိမယ်။  

ပြီးရင် **Login: admin / admin123** (သို့) ဖုန်း **09123456789** နဲ့ ဝင်ပါ။  

---

## ၂။ နောက်ဆိုင်တွေ “ဖွင့်ကြည့်ခြင်း” နည်းနှစ်မျိုး

### ၂.၁ Owner အနေနဲ့ ဆိုင်ရွေးပြီး ကြည့်ခြင်း (Subdomain မသုံးပဲ)

Backend မှာ **ဆိုင်ရွေးပြီး session သတ်မှတ်တဲ့ API** ထည့်ပြီးပါပြီ။  

- **API:** `POST /api/core/set-dashboard-outlet/`  
- **Body:** `{ "outlet_id": 2 }` (ဆိုင်ခွဲ ၂ ကို ရွေးမယ်ဆိုရင်)  
- **အလုပ်:** Session ထဲမှာ ဒီ ဆိုင်ကို သတ်မှတ်ပြီး နောက် API တွေ (Dashboard, Sales, Inventory စသည်) က ဒီ ဆိုင်အလိုက်ပဲ ပြန်မယ်။  
- **ဆိုင်ရွေးချယ်မှု ဖျက်ချင်ရင်:** `POST /api/core/set-dashboard-outlet/` Body `{ "outlet_id": null }` (သို့) outlet_id မပို့ဘဲ ခေါ်ရင် ဆိုင်အားလုံး ပြန်မြင်ရမယ်။  

Frontend မှာ **ဆိုင်ရွေးတဲ့ dropdown** ထည့်ချင်ရင်:

1. `GET /api/core/outlets/` ခေါ်ပြီး ဆိုင်စာရင်း ယူပါ။  
2. Owner ရွေးထားတဲ့ ဆိုင်ကို `POST /api/core/set-dashboard-outlet/` နဲ့ `outlet_id` ပို့ပါ။  
3. နောက် Dashboard / Reports စသည်က ဒီ session ကြောင့် ရွေးထားတဲ့ ဆိုင်အလိုက်ပဲ ပြမယ်။  

(ဒီ API က session သုံးတာမို့ same-origin မှာ session cookie ပို့နေမှ အလုပ်လုပ်မယ်။ CORS / cookie စီမံထားရင် သတိထားပါ။)

### ၂.၂ Subdomain သုံးပြီး ဆိုင်အလိုက် URL ခွဲခြင်း

Demo ကို **subdomain** နဲ့ ခွဲချင်ရင်:

- **Outlet code** နဲ့ **subdomain** ကိုက်ရပါမယ်။  
- Script က ဖန်တီးတဲ့ code တွေ: `MAIN`, `BRANCH_01`, `BRANCH_02`, …  
- ဥပမာ: `main.yourdomain.com` → MAIN ဆိုင်၊ `branch_01.yourdomain.com` → BRANCH_01 ဆိုင်။  

Nginx (သို့) hosting မှာ subdomain တွေကို ဒီ backend ဆီ လှည့်ပေးထားရပါမယ်။  

---

## ၃။ အတိုချုပ်

| လုပ်ချင် တာ | လုပ်ရမည် |
|---------------|------------|
| ဆိုင်သုံးလေးငါးဆိုင် ရှိစေချင် | `python manage.py reset_trial_20_outlets --flush --outlets 3` (သို့) 5 ပြေးပါ။ |
| ဆိုင်ချုပ် ၂၀ + တစ်ချုပ်၌ ခွဲ ၄–၈ ဆိုင် | `--outlets 20 --branches-per-main 4` (သို့) 6 / 8 ပြေးပါ။ စုစုပေါင်း ၂၀ + ၂၀×K ဆိုင် ဖန်တီးမယ်။ |
| တစ်ဆိုင်တည်း ပဲ စမ်းချင် | `--outlets 1` နဲ့ ပြေးပါ။ |
| Owner က ဆိုင်ပြောင်းပြီး ဒေတာကြည့်ချင် | `POST /api/core/set-dashboard-outlet/` ကို `outlet_id` ပို့သုံးပါ (သို့) Frontend မှာ ဆိုင်ရွေးတဲ့ dropdown ထည့်ပြီး ဒီ API ခေါ်ပါ။ |
| Subdomain နဲ့ ဆိုင်အလိုက် URL ခွဲချင် | Outlet code (MAIN_01, MAIN_01_BRANCH_01 စသည်) နဲ့ subdomain ကိုက်အောင် Nginx/hosting စီမံပါ။ |

---

## ၄။ ပစ္စည်း / Categories ထည့်ချင်ရင်

```bash
python manage.py seed_shop_demo --shop general
```

(ဒီ command က ပစ္စည်းနဲ့ categories ထည့်ပေးတာပါ။)
