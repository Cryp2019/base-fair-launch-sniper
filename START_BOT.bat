@echo off
echo ================================================
echo    BASE FAIR LAUNCH SNIPER BOT
echo ================================================
echo.
echo Stopping old Python processes...
taskkill /F /IM python.exe >nul 2>&1
timeout /t 5 /nobreak >nul
echo.
echo Starting bot with FULL SNIPING functionality...
echo.
echo ================================================
echo FEATURES ACTIVE:
echo ================================================
echo [X] Auto-scan every 10 seconds
echo [X] Detect new Uniswap V3 pairs on Base
echo [X] Send alerts to all users
echo [X] Premium priority alerts
echo [X] Wallet creation
echo [X] Manual token checking
echo ================================================
echo.
echo Bot is starting...
echo DO NOT CLOSE THIS WINDOW!
echo.
python sniper_bot.py
pause

