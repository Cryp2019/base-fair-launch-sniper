@echo off
REM Bot Restart Script
REM This script stops any running bot instances and starts fresh

echo ========================================
echo   RESTARTING BASE SNIPER BOT
echo ========================================
echo.

echo [1/3] Stopping any running bot instances...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *sniper*" 2>nul
timeout /t 2 /nobreak >nul

echo [2/3] Starting bot with updated code...
echo.
python sniper_bot.py

echo.
echo ========================================
echo   BOT STOPPED
echo ========================================
pause
