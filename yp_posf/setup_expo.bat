@echo off
REM Expo Go Setup Script for Windows
REM Run: setup_expo.bat

echo === Expo Go Setup ===
echo.

cd /d "%~dp0"

echo 1) Installing dependencies...
call npm install
if errorlevel 1 (
  echo Installation failed
  pause
  exit /b 1
)

echo.
echo === Setup Complete ===
echo.
echo Next steps:
echo 1. Start Vue dev server: npm run dev
echo 2. Start Expo: npm run expo:start:tunnel
echo 3. Scan QR code with Expo Go app
echo.
echo Or use separate terminals:
echo   Terminal 1: npm run dev
echo   Terminal 2: npm run expo:start:tunnel
echo   Terminal 3: python manage.py runserver 0.0.0.0:8000
echo.
pause
