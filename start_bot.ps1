# Safe Bot Startup Script
# Ensures only one instance runs at a time

Write-Host "🤖 Base Fair Launch Sniper - Safe Startup" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Check for existing Python processes
Write-Host "🔍 Checking for existing bot instances..." -ForegroundColor Yellow
$pythonProcesses = Get-Process python -ErrorAction SilentlyContinue

if ($pythonProcesses) {
    Write-Host "⚠️  Found $($pythonProcesses.Count) Python process(es) running" -ForegroundColor Yellow
    Write-Host "🛑 Stopping all Python processes..." -ForegroundColor Red
    
    Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
    Start-Sleep -Seconds 2
    
    Write-Host "✅ All Python processes stopped" -ForegroundColor Green
} else {
    Write-Host "✅ No existing Python processes found" -ForegroundColor Green
}

Write-Host ""
Write-Host "🚀 Starting bot..." -ForegroundColor Cyan
Write-Host ""

# Change to bot directory
Set-Location -Path "e:\base-fair-launch-sniper"

# Start the bot
python sniper_bot.py
