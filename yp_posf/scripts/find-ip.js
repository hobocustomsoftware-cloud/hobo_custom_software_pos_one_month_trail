#!/usr/bin/env node
/**
 * Helper script to find your local IP address for Expo Go testing
 * Run: node scripts/find-ip.js
 */

const os = require('os');

function getLocalIP() {
  const interfaces = os.networkInterfaces();
  const addresses = [];

  for (const name of Object.keys(interfaces)) {
    for (const iface of interfaces[name]) {
      // Skip internal (loopback) and non-IPv4 addresses
      if (iface.family === 'IPv4' && !iface.internal) {
        addresses.push({
          name,
          address: iface.address,
        });
      }
    }
  }

  return addresses;
}

const ips = getLocalIP();

if (ips.length === 0) {
  console.log('❌ No local IP address found');
  process.exit(1);
}

console.log('\n📱 Expo Go Testing - Local IP Addresses:\n');
ips.forEach(({ name, address }) => {
  console.log(`  ${name}: ${address}`);
});

const primaryIp = ips[0].address;
console.log(`\n✅ Primary IP: ${primaryIp}\n`);

console.log('📝 Update app.json:\n');
console.log(`  "extra": {`);
console.log(`    "apiUrl": "http://${primaryIp}:8000/api",`);
console.log(`    "localIp": "${primaryIp}",`);
console.log(`    ...`);
console.log(`  }\n`);

console.log('🔧 Or set environment variable:');
console.log(`  EXPO_LOCAL_IP=${primaryIp} npm run expo:start\n`);
