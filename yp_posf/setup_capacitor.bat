@echo off
REM Capacitor Setup Script for Windows
REM Run: setup_capacitor.bat

echo === Capacitor Mobile App Setup ===
echo.

cd /d "%~dp0"

echo 1) Building Vue app...
call npm run build
if errorlevel 1 (
  echo Build failed
  pause
  exit /b 1
)

echo.
echo 2) Initializing Capacitor (if not done)...
if not exist "capacitor.config.ts" (
  echo Capacitor config not found. Please run: npx cap init
  echo App ID: com.hobopos.app
  echo App Name: HoBo POS
  echo Web Dir: dist
  pause
  exit /b 1
)

echo.
echo 3) Syncing to native projects...
call npm run cap:sync
if errorlevel 1 (
  echo Sync failed
  pause
  exit /b 1
)

echo.
echo === Setup Complete ===
echo.
echo Next steps:
echo - iOS: npm run cap:ios (requires macOS + Xcode)
echo - Android: npm run cap:android (requires Android Studio)
echo.
pause
