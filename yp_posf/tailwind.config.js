/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        // Reference design: teal/light blue accent (POS.COM style)
        'pos-teal': { DEFAULT: '#0d9488', 600: '#0d9488', 700: '#0f766e', 500: '#14b8a6' },
      },
      fontFamily: {
        sans: ['Inter', 'SF Pro Text', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        display: ['Inter', 'SF Pro Display', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
      },
      backgroundImage: {
        'dashboard-deep': 'linear-gradient(135deg, #aa0000 0%, #151515 100%)',
      },
      boxShadow: {
        'glow-sm': '0 0 20px -5px rgba(255, 255, 255, 0.08), 0 0 40px -10px rgba(255, 255, 255, 0.04)',
        'glow': '0 0 30px -5px rgba(255, 255, 255, 0.1), 0 0 60px -15px rgba(255, 255, 255, 0.06)',
        'glow-lg': '0 0 40px -5px rgba(255, 255, 255, 0.12), 0 0 80px -20px rgba(255, 255, 255, 0.08)',
      },
    },
  },
  plugins: [],
}
