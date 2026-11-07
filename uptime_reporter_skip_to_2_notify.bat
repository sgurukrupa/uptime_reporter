@echo off
start "" "%~dp0.venv\Scripts\pythonw.exe" "%~dp0uptime_reporter.py" --skip-boots 2 --notify 8h30m %*
