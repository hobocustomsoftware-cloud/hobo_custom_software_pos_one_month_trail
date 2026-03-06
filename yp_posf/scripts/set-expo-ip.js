#!/usr/bin/env node
/**
 * app.json ထဲက expo.extra.apiUrl နဲ့ expo.extra.localIp ကို လက်ရှိ ကွန်ပျူတာ IP နဲ့ အလိုအလျောက် ပြင်ပေးမယ်
 * Expo Go စမ်းတဲ့အခါ ဖုန်းက ဒီ IP နဲ့ Vue dev server နဲ့ Backend ကို ချိတ်မယ်
 * Run: node scripts/set-expo-ip.js
 */

import fs from 'fs';
import path from 'path';
import os from 'os';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

function getLocalIP() {
  const interfaces = os.networkInterfaces();
  for (const name of Object.keys(interfaces)) {
    for (const iface of interfaces[name]) {
      if (iface.family === 'IPv4' && !iface.internal) {
        return iface.address;
      }
    }
  }
  return null;
}

const appJsonPath = path.join(__dirname, '..', 'app.json');
let data;

try {
  data = JSON.parse(fs.readFileSync(appJsonPath, 'utf8'));
} catch (e) {
  console.error('app.json ဖတ်မရပါ:', e.message);
  process.exit(1);
}

const ip = getLocalIP();
if (!ip) {
  console.error('Local IP မတွေ့ပါ။');
  process.exit(1);
}

if (!data.expo) data.expo = {};
if (!data.expo.extra) data.expo.extra = {};

data.expo.extra.apiUrl = `http://${ip}:8000/api`;
data.expo.extra.localIp = ip;
if (!data.expo.extra.appUrl) {
  data.expo.extra.appUrl = 'https://your-domain.com/app/';
}

fs.writeFileSync(appJsonPath, JSON.stringify(data, null, 2), 'utf8');
console.log('app.json ပြင်ပြီးပါပြီ။');
console.log('  localIp:', ip);
console.log('  apiUrl: http://' + ip + ':8000/api');
console.log('\nExpo Go စမ်းရန်: npm run expo:start (သို့) npm run expo:start:tunnel');
