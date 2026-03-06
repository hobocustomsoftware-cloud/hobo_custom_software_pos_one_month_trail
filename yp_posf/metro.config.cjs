// Metro config must use CommonJS (not ES modules)
// Rename to metro.config.cjs or use .cjs extension
const { getDefaultConfig } = require('expo/metro-config');

const config = getDefaultConfig(__dirname);

module.exports = config;
