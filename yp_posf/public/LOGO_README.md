# Logo ထည့်သွင်းခြင်း

**ဤနေရာတွင် logo ဖိုင်ကို ထည့်ပါ:**

```
yp_posf/public/logo.svg   (သို့မဟုတ် logo.png)
```

- ဖိုင်အမည်: `logo.svg` သို့မဟုတ် `logo.png`
- နေရာ: `yp_posf/public/` ဖိုလ်ဒါအတွင်း
- Favicon: `index.html` က `/logo.png` သုံးသည်။ `logo.png` မရှိရင် `npm run build` က placeholder ထုတ်ပေးမည်။ HoBo icon ပြချင်ရင် `public/logo.png` ကို 32×32 သို့မဟုတ် 64×64 PNG ဖြင့် အစားထိုးပါ။
- သင့်လိုချင်သော logo ဖြင့် အစားထိုးပါ

**EXE & Installer:**
- `logo.png` ရှိရင် `deploy/exe/make_icon.py` က `logo.ico` ဖန်တီးပါမယ်
- `logo.svg` ရှိရင် cairosvg ရှိရင် ico ပြောင်းပါမယ် (`pip install cairosvg`)
- `logo.ico` က EXE နဲ့ Windows shortcut icon အတွက် သုံးပါတယ်

Logo ထည့်ပြီးပါက Vue app နှင့် EXE shortcut မှာ အလိုအလျောက် ပြသမည်။
