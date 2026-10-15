@echo off
rem Start Squad Ballistics from source (no build needed).
cd /d "%~dp0"
if not exist venv\Scripts\python.exe call setup.bat
venv\Scripts\python.exe app.py
if errorlevel 1 pause
