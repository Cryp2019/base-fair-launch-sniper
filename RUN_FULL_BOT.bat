@echo off
cls
echo ========================================================
echo           BASE FAIR LAUNCH SNIPER BOT
echo                  FULL VERSION
echo ========================================================
echo.
echo Stopping any old Python processes...
taskkill /F /IM python.exe >nul 2>&1
timeout /t 3 /nobreak >nul
echo.
echo ========================================================
echo                 FEATURES ACTIVE
echo ========================================================
echo.
echo [X] AUTOMATIC SNIPING
echo     - Scans Base every 10 seconds
echo     - Detects new Uniswap V3 pairs
echo     - Sends alerts to all users
echo     - Premium priority alerts
echo.
echo [X] MANUAL SNIPING
echo     - User clicks "Snipe Token" button
echo     - Paste any token address
echo     - Get instant analysis
echo     - Direct Uniswap links
echo.
echo [X] WALLET MANAGEMENT
echo     - Create Base wallets
echo     - Export private keys
echo     - Secure storage
echo.
echo [X] OTHER FEATURES
echo     - Manual token checking
echo     - Referral system
echo     - Premium tiers
echo     - Leaderboard
echo     - Stats tracking
echo.
echo ========================================================
echo.
echo Starting FULL bot now...
echo.
echo DO NOT CLOSE THIS WINDOW!
echo The bot needs to stay running 24/7
echo.
echo ========================================================
echo.
python sniper_bot.py
echo.
echo ========================================================
echo Bot stopped!
echo ========================================================
pause

