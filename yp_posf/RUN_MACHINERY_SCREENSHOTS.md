# Machinery Shop Screenshots – လုပ်နည်း

## အကောင်းဆုံး: တစ်ခါတည်း (ကျွန်တော်တို့က လုပ်ပေးထားတာ)

**Repo root** မှာ ဒီ **ဖိုင်တစ်ခုတည်း** run ရင် Backend + Frontend ကိုယ်တိုင် စတင်ပြီး screenshot ရိုက်မယ်။ Terminal သုံးခု မလိုပါ။

### နည်း ၁ – Batch ဖိုင်နဲ့ (double-click သို့ cmd မှာ)

```
F:\hobo_license_pos\run_machinery_screenshots.bat
```

Double-click လုပ်ပါ သို့မဟုတ် cmd မှာ:

```bash
cd F:\hobo_license_pos
run_machinery_screenshots.bat
```

### နည်း ၂ – Node တိုက်ရိုက်

```bash
cd F:\hobo_license_pos
node run_all_machinery.mjs
```

ဒီ script က:
1. Backend (Django/Uvicorn :8000) စတင်မယ်  
2. Frontend (Vite :5173) စတင်မယ်  
3. နှစ်ခုလုံး စောင့်မယ်  
4. Machinery Shop simulation (၇ ရက်) ပြေးပြီး screenshot ရိုက်မယ်  
5. ပုံတွေက `yp_posf\simulations\machinery_shop\` မှာ သိမ်းမယ်  

---

## လိုအပ်ချက်များ

- **Node** (npm ပါရမယ်)  
- **Python** + Django, uvicorn (သို့ run_lite.bat သုံးတဲ့ venv)  
- **Playwright** – တစ်ကြိမ်ပဲ: `cd yp_posf` ပြီး `npm install playwright` နဲ့ `npx playwright install chromium`  

---

## ပုံတွေ ဘယ်မှာ ထွက်မလဲ

- **Folder:** `F:\hobo_license_pos\yp_posf\simulations\machinery_shop\`  
- **ဖိုင်များ:** `1.png` … `7.png` နဲ့ `3_insight.png`, `7_insight.png`  

---

## ရွေးချယ်စရာ: Terminal သုံးခု ကိုယ်တိုင် ဖွင့်ပြီး လုပ်မယ်

Backend စတင် → Frontend စတင် → `cd yp_posf` ပြီး `node simulate_machinery_shop.js` ပြေးပါ။ အသေးစိတ်က ဒီစာရွက်ရဲ့ အောက်ပိုင်းမှာ ရှိပါတယ်။
