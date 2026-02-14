# Debug Instructions

I have pushed a debug update to `sniper_bot.py` that will list the files in the Railway directory at startup. This will help diagnose why `project_sponsors` and `onchain_analyzer` are failing to import despite being in the repository.

## Action Required

1.  **Restart the bot** (it should restart automatically after the recent deploy).
2.  **Check the logs** for lines starting with `📂`.
    -   If these lines show `project_sponsors.py` and `onchain_analyzer.py` are present in `Files in CWD`, then it's a python path or permissions issue.
    -   If they are missing from the list, then the deployment is not picking them up (possibly due to `.dockerignore` excludes or volume mounting issues masking the files).
3.  **Confirm functionality**: Even with the warnings, basic Monad posting should now work (RPC connection confirmed). Please check if new tokens are being posted to your group.

Check the logs on your Railway dashboard.
