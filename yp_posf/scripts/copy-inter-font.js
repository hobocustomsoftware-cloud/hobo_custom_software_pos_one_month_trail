#!/usr/bin/env node
/**
 * Copy Inter variable font from @fontsource-variable/inter to public/fonts/
 * so the app can serve it locally and avoid Google Fonts timeout during simulation.
 * Run automatically via npm run prepare (after npm install).
 */
const fs = require('fs')
const path = require('path')

const projectRoot = path.resolve(__dirname, '..')
const packagePath = path.join(projectRoot, 'node_modules', '@fontsource-variable', 'inter', 'files', 'inter-latin-wght-normal.woff2')
const outDir = path.join(projectRoot, 'public', 'fonts')
const outPath = path.join(outDir, 'Inter.var.woff2')

if (!fs.existsSync(packagePath)) {
  console.warn('copy-inter-font: @fontsource-variable/inter not found. Run: npm install @fontsource-variable/inter --save-dev')
  process.exit(0)
}

fs.mkdirSync(outDir, { recursive: true })
fs.copyFileSync(packagePath, outPath)
console.log('Inter font copied to public/fonts/Inter.var.woff2')
