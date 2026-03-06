# License System

## Overview

- **Trial:** ၁ လ (၃၀ ရက်) + ၅ ရက် grace period (Server + Installation နှစ်မျိုးလုံး)
- **On-Premise:** တစ်ခါဝယ် အမြဲသုံး (perpetual)
- **Hosted:** တစ်နှစ်တစ်ခါ renewal

## Machine ID (Trial မပြန်စအောင်)

- **Server (Docker):** `data/machine_id` ဖိုင်သိမ်း (license_data volume) - container restart လုပ်ရင်လည်း မပြောင်း
- **Server (Env):** `MACHINE_ID=xxx` သတ်မှတ်ထားနိုင်သည်
- **Installation:** Platform-based (hostname, etc.) - စက်တိုင်းမှာ မတူညီ

## License Key ဖန်တီးခြင်း

### Option 1: Standalone (Django မလို)

```bash
cd license_generator
python generate_license.py --type on_premise_perpetual
python generate_license.py --type hosted_annual --years 1 --sql
```

### Option 2: Django Management Command

```bash
cd WeldingProject
python manage.py create_license --type on_premise_perpetual
python manage.py create_license --type hosted_annual --years 1
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/license/status/` | GET | License status စစ်ဆေးခြင်း |
| `/api/license/activate/` | POST | License key ထည့်ပြီး activate လုပ်ခြင်း |

## Activation Flow

1. User က `/license-activate` သို့ သွားသည် (Vue) သို့မဟုတ် license ကုန်ပြီး 403 ရရင် auto redirect
2. License key ထည့်ပြီး Activate နှိပ်သည်
3. Backend က DB မှာ စစ်ဆေးပြီး `license.lic` ဖိုင်သိမ်းသည် (On-Premise offline အတွက်)

## Environment

| Variable | Description |
|----------|-------------|
| `DEPLOYMENT_MODE` | `on_premise` (default) or `hosted` |
| `MACHINE_ID` | Server (Docker) မှာ သတ်မှတ်ထားနိုင်သည်။ မထည့်ရင် `data/machine_id` မှ auto |
| `SKIP_LICENSE` | `true` ထားရင် license မစစ် (dev အတွက်) |

## Admin

- Django Admin မှ `AppLicense` နဲ့ `AppInstallation` ကို စီမံခန့်ခွဲနိုင်သည်
- License key ကို Admin မှ လက်ဖြင့် ထည့်သွင်းနိုင်သည်
