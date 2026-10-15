@echo off
rem Run the automatic tests.
cd /d "%~dp0"
if not exist venv\Scripts\python.exe call setup.bat
venv\Scripts\python.exe -m pytest -q
pause
