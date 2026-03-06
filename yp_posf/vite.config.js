import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueJsx from '@vitejs/plugin-vue-jsx'
import vueDevTools from 'vite-plugin-vue-devtools'
import tailwindcss from '@tailwindcss/vite'

const srcDir = fileURLToPath(new URL('./src', import.meta.url))

// https://vite.dev/config/
export default defineConfig(({ command }) => ({
  base: process.env.VITE_BASE || '/',  // '/' or '/app/' (Django: /app/ + /assets/; stops 404 on hashed assets when mapping correct)
  plugins: [
    vue(),
    vueJsx(),
    ...(command === 'serve' ? [vueDevTools()] : []),
    tailwindcss(),
  ],
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    rollupOptions: {
      output: {
        manualChunks: (id) => {
          // Vue core နဲ့ heavy lib တွေကို vendor chunk ခွဲခြား → page chunk တွေ သေးစေရန်
          if (id.includes('node_modules/vue/') || id.includes('node_modules/@vue/')) return 'vue'
          if (id.includes('node_modules/vue-router/')) return 'vue-router'
          if (id.includes('node_modules/pinia/')) return 'pinia'
          if (id.includes('node_modules/apexcharts') || id.includes('node_modules/vue3-apexcharts')) return 'apexcharts'
          if (id.includes('node_modules/jsbarcode') || id.includes('node_modules/html5-qrcode')) return 'barcode-qr'
        },
      },
    },
    chunkSizeWarningLimit: 600,
  },
  resolve: {
    alias: {
      '@': srcDir,
    },
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '/api'),
      },
    },
  },
}))
