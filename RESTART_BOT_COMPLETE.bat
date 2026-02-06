@echo off
REM Complete Bot Restart - Kills all Python and starts fresh
echo ========================================
echo   COMPLETE BOT RESTART
echo ========================================
echo.

echo [1/3] Killing ALL Python processes...
taskkill /F /IM python.exe 2>nul
timeout /t 3 /nobreak >nul

echo [2/3] Verifying Python is stopped...
tasklist /FI "IMAGENAME eq python.exe" 2>nul | find /I /N "python.exe">nul
if "%ERRORLEVEL%"=="0" (
    echo WARNING: Python still running, trying again...
    taskkill /F /IM python.exe /T 2>nul
    timeout /t 2 /nobreak >nul
)

echo [3/3] Starting bot with NEW code...
echo.
echo ========================================
echo   BOT IS STARTING...
echo ========================================
echo.
python sniper_bot.py

echo.
echo ========================================
echo   BOT STOPPED
echo ========================================
pause
