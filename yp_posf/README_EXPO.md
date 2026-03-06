# Expo Go Quick Start

## 🚀 Quick Setup

### 1. Install Dependencies
```bash
cd yp_posf
npm install
```

### 2. Start Vue Dev Server (Terminal 1)
```bash
npm run dev
# Runs on http://localhost:5173
```

### 3. Start Expo (Terminal 2)
```bash
npm run expo:start:tunnel
# Shows QR code
```

### 4. Start Backend (Terminal 3)
```bash
cd ../WeldingProject
python manage.py runserver 0.0.0.0:8000
```

### 5. Connect with Expo Go
1. Install **Expo Go** app on your phone
2. Scan QR code from Terminal 2
3. App loads in Expo Go!

## 📱 Configuration

### For Local Network Testing:
1. Find your computer's IP:
   - Windows: `ipconfig`
   - Mac/Linux: `ifconfig`

2. Update `App.js` (line ~30):
   ```javascript
   const viteUrl = 'http://192.168.1.XXX:5173'; // Your IP
   ```

3. Update `app.json`:
   ```json
   "extra": {
     "apiUrl": "http://192.168.1.XXX:8000/api"
   }
   ```

### For Tunnel (Easiest):
Just use `npm run expo:start:tunnel` - no IP config needed!

## ⚠️ Important Notes

- **Vue dev server** must be running (`npm run dev`)
- **Backend** must run on `0.0.0.0:8000` (not `127.0.0.1`)
- **Phone and computer** must be on same WiFi (unless using tunnel)
- **Expo Go** app must be installed on phone

## 🎯 Features That Work

✅ Login/Register  
✅ Sales POS  
✅ Inventory  
✅ Reports  
✅ Accounting & P&L  
✅ Payment Methods  
✅ QR Scanning  
✅ Camera Upload  

## 📖 Full Documentation

See `docs/EXPO_GO_SETUP.md` for detailed guide.
