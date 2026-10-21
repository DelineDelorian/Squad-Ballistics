@echo off
rem Build the single-file dist\SquadBallistics.exe and check that it works.
setlocal
cd /d "%~dp0"
if not exist venv\Scripts\python.exe call setup.bat

echo Building...
venv\Scripts\python.exe -m PyInstaller --noconfirm --clean SquadBallistics.spec || goto :fail

echo Checking the build...
del /q dist\selftest.log 2>nul
start "" /wait dist\SquadBallistics.exe --selftest
type dist\selftest.log
findstr /c:"SELFTEST PASSED" dist\selftest.log >nul || goto :fail
del /q dist\selftest.log

echo.
echo Done: dist\SquadBallistics.exe
explorer /select,"dist\SquadBallistics.exe"
pause
exit /b 0

:fail
echo.
echo [ERROR] Build failed, see the messages above.
pause
exit /b 1
