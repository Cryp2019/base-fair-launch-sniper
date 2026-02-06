#!/usr/bin/env python3
"""
Force Kill and Restart Bot
This script will forcefully stop all Python processes and restart the bot
"""
import os
import sys
import time
import subprocess
import psutil

def kill_all_python():
    """Kill all Python processes except this one"""
    current_pid = os.getpid()
    killed = []
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['name'] and 'python' in proc.info['name'].lower():
                if proc.info['pid'] != current_pid:
                    print(f"Killing Python process PID {proc.info['pid']}: {proc.info['cmdline']}")
                    proc.kill()
                    killed.append(proc.info['pid'])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    return killed

def main():
    print("=" * 70)
    print("FORCE RESTART BOT")
    print("=" * 70)
    print()
    
    # Step 1: Kill all Python processes
    print("[1/3] Stopping all Python processes...")
    killed = kill_all_python()
    if killed:
        print(f"   ✅ Killed {len(killed)} Python process(es)")
    else:
        print("   ℹ️  No Python processes found")
    
    # Step 2: Wait for processes to fully terminate
    print("\n[2/3] Waiting for processes to terminate...")
    time.sleep(3)
    
    # Step 3: Start the bot
    print("\n[3/3] Starting bot with NEW code...")
    print()
    print("=" * 70)
    print("BOT STARTING...")
    print("=" * 70)
    print()
    
    # Start the bot
    os.system("python sniper_bot.py")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Restart cancelled")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        input("Press Enter to exit...")
