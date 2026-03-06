import React, { useState, useEffect } from 'react';
import { View, StyleSheet, ActivityIndicator, Text, SafeAreaView } from 'react-native';
import { WebView } from 'react-native-webview';
import Constants from 'expo-constants';
import * as Network from 'expo-network';
import { StatusBar } from 'expo-status-bar';

// Get API URL from Expo config
const API_URL = Constants.expoConfig?.extra?.apiUrl || 'http://localhost:8000/api';

export default function App() {
  const [webViewUrl, setWebViewUrl] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Determine the URL to load
    // In development: Use your computer's IP or localhost (if using Expo tunnel)
    // In production: Use your hosted backend URL
    
    const determineUrl = async () => {
      try {
        // Check if we're in development mode
        if (__DEV__) {
          // Get local IP from Expo config or environment
          // Set EXPO_LOCAL_IP in app.json extra or use default
          const localIp = Constants.expoConfig?.extra?.localIp || null;
          
          // Option 1: Use Expo tunnel (works on any network, no IP needed)
          // Run: npm run expo:start:tunnel
          // Then use localhost (Expo tunnel handles routing)
          
          // Option 2: Use your computer's local IP (for same WiFi network)
          // Set in app.json: "extra": { "localIp": "192.168.1.100" }
          // Or find IP: ipconfig (Windows) / ifconfig (Mac/Linux)
          
          // IMPORTANT: Use Vue dev server (port 5173) for development
          // This ensures hot reload and proper asset serving
          const viteUrl = localIp 
            ? `http://${localIp}:5173`
            : 'http://localhost:5173'; // Default: localhost (works with tunnel)
          
          // Alternative: Use Django-served built version (if Vue dev server not running)
          // const builtUrl = localIp 
          //   ? `http://${localIp}:8000/app/`
          //   : 'http://localhost:8000/app/';
          
          setWebViewUrl(viteUrl);
        } else {
          // Production: Use your hosted backend URL
          // The Vue app should be served from your backend or CDN
          setWebViewUrl('https://your-domain.com/app/');
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    determineUrl();
  }, []);

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#f59e0b" />
          <Text style={styles.loadingText}>HoBo POS စတင်နေသည်...</Text>
        </View>
        <StatusBar style="light" />
      </SafeAreaView>
    );
  }

  if (error) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.errorContainer}>
          <Text style={styles.errorText}>Error: {error}</Text>
          <Text style={styles.errorHint}>
            Make sure your Vue app is running.{'\n'}
            Development: npm run dev (in yp_posf folder){'\n'}
            Or update webViewUrl in App.js
          </Text>
        </View>
        <StatusBar style="light" />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <WebView
        source={{ uri: webViewUrl }}
        style={styles.webview}
        javaScriptEnabled={true}
        domStorageEnabled={true}
        startInLoadingState={true}
        scalesPageToFit={true}
        allowsInlineMediaPlayback={true}
        mediaPlaybackRequiresUserAction={false}
        onError={(syntheticEvent) => {
          const { nativeEvent } = syntheticEvent;
          console.warn('WebView error: ', nativeEvent);
          setError(`Cannot load app: ${nativeEvent.description || 'Unknown error'}`);
        }}
        onHttpError={(syntheticEvent) => {
          const { nativeEvent } = syntheticEvent;
          console.warn('WebView HTTP error: ', nativeEvent);
        }}
        onLoadEnd={() => {
          setLoading(false);
        }}
        // Inject API URL into the Vue app
        injectedJavaScript={`
          (function() {
            // Set API URL for Vue app
            window.EXPO_API_URL = '${API_URL}';
            // Signal that Expo environment is ready
            window.EXPO_READY = true;
            console.log('Expo WebView loaded, API URL:', '${API_URL}');
          })();
          true; // Required for iOS
        `}
      />
      <StatusBar style="light" />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1a1a1a',
  },
  webview: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#1a1a1a',
  },
  loadingText: {
    marginTop: 16,
    color: '#ffffff',
    fontSize: 16,
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
    backgroundColor: '#1a1a1a',
  },
  errorText: {
    color: '#ef4444',
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 16,
    textAlign: 'center',
  },
  errorHint: {
    color: '#9ca3af',
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 20,
  },
});
