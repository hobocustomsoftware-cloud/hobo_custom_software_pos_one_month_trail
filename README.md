# HoBo POS – တစ်လ Trial (One Month Trial)

POS System တစ်လ အစမ်းသုံး ဗားရှင်း။ Google Cloud (VM / Cloud Run) သို့ တင်ရန် ဒီ folder ကိုသုံးပါ။

## ပါဝင်သည်များ

- **WeldingProject/** – Django backend (API, DB, license trial)
- **yp_posf/** – Vue frontend (POS UI)
- **compose/** – Docker Compose (Postgres + Redis + Backend + Frontend)
- **scripts/** – Rebuild / run scripts

## Docker ဖြင့် စတင်ရန်

```bash
cd one_month_trial
# ပထမ frontend build လုပ်ပါ (dist လိုအပ်သည်)
cd yp_posf && npm ci && npm run build && cd ..
docker compose -f compose/docker-compose.yml up -d --build
```

- Frontend: http://localhost:8888/app/
- Backend API: http://localhost:8001/api/

Port ပြောင်းချင်ရင် `.env` မှာ `FRONTEND_PORT`, `BACKEND_PORT` သတ်မှတ်ပါ။

## Google Cloud instance မှာ တင်ရန်

1. ဒီ repo ကို instance ပေါ် clone ပါ။
2. `.env` ဖိုင်ဖန်တီးပြီး အနည်းဆုံး DJANGO_SECRET_KEY နှင့် DJANGO_ALLOWED_HOSTS ထည့်ပါ။ DJANGO_ALLOWED_HOSTS=* သို့မဟုတ် instance IP/domain (မထည့်ရင် Login/Register မှာ 400 ဖြစ်နိုင်သည်)။
3. Frontend build: cd yp_posf && npm ci && npm run build && cd ..
4. docker compose -f compose/docker-compose.yml up -d --build ပြေးပါ။
5. Firewall / Security rules မှာ 8888 (သို့) သင်သတ်မှတ်ထားသော port ဖွင့်ပါ။
Login/Register မှာ 400 ဖြစ်နေရင်: .env မှာ DJANGO_ALLOWED_HOSTS=* သို့မဟုတ် instance IP ထည့်ပြီး docker compose ... up -d --force-recreate backend ပြန်ပြေးပါ။

## ဆိုင်တစ်ဆိုင်ချင်း နှင့် ဆိုင်ခွဲများ (Outlets / Branches)

Trial မှာ **ဆိုင်တစ်ချင်း** (တစ်ဆိုင်တည်း) သို့မဟုတ် **ဆိုင်ခွဲများ** ဖွင့်ပြီး စမ်းလို့ ရပါသည်။

- **တစ်ဆိုင်တည်း:** ဆိုင်ချုပ် ၁ ခုတည်း
- **ဆိုင်ခွဲပါ:** ဆိုင်ချုပ် ၁ ခု + ဆိုင်ခွဲ ၂၊ ၃၊ ၄ သို့မဟုတ် ၁၉ ခု (စုစုပေါင်း ၃/၄/၅/၂၀ ဆိုင်)

Backend container ထဲမှာ (သို့) migrate ပြီးချိန် အတွင်းမှာ အောက်ပါ command ဖြင့် သတ်မှတ်ပါ။

Command (backend container): python manage.py reset_trial_20_outlets --flush --outlets 1 (တစ်ဆိုင်တည်း) or --outlets 3/5/20 (ဆိုင်ခွဲပါ). Login: admin / admin123. ဆိုင်ခွဲ စီမံ: App → Settings → Shop Locations / ဆိုင်ခွဲ.

- Login: **admin** / **admin123**
- ဆိုင်ခွဲများ စီမံရန်: App ထဲမှာ **Settings → Shop Locations / ဆိုင်ခွဲ** (သို့) **Locations / ဆိုင်ခွဲ** သို့ သွားပါ။
- ရောင်းချရန် ဆိုင်ရွေးချယ်ခြင်း၊ ဝယ်ယူမည့်ဆိုင်ရွေးချယ်ခြင်း စသည်ဖြင့် ဆိုင်အလိုက် သုံးလို့ ရပါသည်။

## GitHub Trial Repo

ဒီ folder ကို အောက်ပါ repo သို့ push လို့ ရပါသည်။

- https://github.com/hobocustomsoftware-cloud/hobo_custom_software_pos_one_month_trail

```bash
cd one_month_trial
git init
git remote add origin https://github.com/hobocustomsoftware-cloud/hobo_custom_software_pos_one_month_trail.git
git add -A
git commit -m "POS One Month Trial"
git branch -M main
git push -u origin main
```
