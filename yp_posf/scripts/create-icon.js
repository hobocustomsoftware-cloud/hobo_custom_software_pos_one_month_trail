// Simple script to create a placeholder icon.png
// Run: node scripts/create-icon.js

const fs = require('fs');
const path = require('path');

// Create a minimal valid 1x1 PNG (will be replaced with proper icon later)
// This is a base64 encoded 1x1 transparent PNG
const iconBase64 = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==';

const assetsDir = path.join(__dirname, '..', 'assets');
const iconPath = path.join(assetsDir, 'icon.png');

if (!fs.existsSync(assetsDir)) {
  fs.mkdirSync(assetsDir, { recursive: true });
}

const iconBuffer = Buffer.from(iconBase64, 'base64');
fs.writeFileSync(iconPath, iconBuffer);

console.log('✅ Icon created at:', iconPath);
console.log('⚠️  This is a placeholder. Replace with a proper 1024x1024 PNG icon.');
