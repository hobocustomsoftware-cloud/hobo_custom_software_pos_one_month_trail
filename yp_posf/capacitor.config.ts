import { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.hobopos.app',
  appName: 'HoBo POS',
  webDir: 'dist',
  server: {
    // Development: Use local backend (change to your computer's IP for physical device)
    // For iOS Simulator: http://localhost:8000 works
    // For physical device: http://192.168.1.XXX:8000 (your computer's local IP)
    // Production: Use your hosted backend URL (e.g., https://your-domain.com)
    url: process.env.CAPACITOR_SERVER_URL || 'http://localhost:8000',
    cleartext: true, // Allow HTTP (for local development, set false for HTTPS)
  },
  plugins: {
    Camera: {
      permissions: {
        camera: 'HoBo POS needs camera access to scan QR codes and take photos.',
        photos: 'HoBo POS needs photo library access to select images.',
      },
    },
  },
  ios: {
    contentInset: 'automatic',
    scrollEnabled: true,
    // For production: uncomment and set your bundle identifier
    // scheme: 'hobopos',
  },
  android: {
    allowMixedContent: true,
    captureInput: true,
    // For production: uncomment and set your package name
    // buildOptions: {
    //   keystorePath: 'path/to/keystore.jks',
    //   keystorePassword: 'your-password',
    // },
  },
};

export default config;
