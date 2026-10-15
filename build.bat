@echo off
rem Build the .exe into dist\SquadBallistics and pack dist\SquadBallistics.zip
rem (the zip has the same layout as the GitHub release used by the updater).
setlocal
cd /d "%~dp0"
if not exist venv\Scripts\python.exe call setup.bat

echo Building...
venv\Scripts\python.exe -m PyInstaller --noconfirm --clean SquadBallistics.spec || goto :fail

echo Checking the build...
del /q dist\SquadBallistics\selftest.log 2>nul
start "" /wait dist\SquadBallistics\SquadBallistics.exe --selftest
type dist\SquadBallistics\selftest.log
findstr /c:"SELFTEST PASSED" dist\SquadBallistics\selftest.log >nul || goto :fail

echo Packing dist\SquadBallistics.zip...
powershell -NoProfile -Command "Compress-Archive -Path 'dist\SquadBallistics' -DestinationPath 'dist\SquadBallistics.zip' -Force" || goto :fail

echo.
echo Done: dist\SquadBallistics\SquadBallistics.exe
explorer dist\SquadBallistics
pause
exit /b 0

:fail
echo.
echo [ERROR] Build failed, see the messages above.
pause
exit /b 1
