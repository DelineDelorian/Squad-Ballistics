@echo off
rem One-time setup: finds (or installs) Python and installs all dependencies
rem into a local "venv" folder. Safe to run again.
setlocal
cd /d "%~dp0"

call :find_python
if not defined PY (
    echo Python was not found. Installing Python 3.12 with winget...
    winget install -e --id Python.Python.3.12 --scope user --accept-package-agreements --accept-source-agreements
    call :find_python
)
if not defined PY (
    echo.
    echo [ERROR] Python is still not available.
    echo Install Python 3.12 from https://www.python.org/downloads/
    echo and tick "Add python.exe to PATH", then run setup.bat again.
    pause
    exit /b 1
)

echo Using %PY%
if not exist venv\Scripts\python.exe (
    %PY% -m venv venv || goto :fail
)

venv\Scripts\python.exe -m pip install --upgrade pip || goto :fail
venv\Scripts\python.exe -m pip install -r requirements-dev.txt || goto :fail

echo.
echo Setup complete.
echo   run.bat    - start Squad Ballistics from source
echo   build.bat  - build dist\SquadBallistics\SquadBallistics.exe
echo   test.bat   - run the automatic tests
pause
exit /b 0

:find_python
set "PY="
py -3.12 -c "import sys" >nul 2>nul && set "PY=py -3.12" && goto :eof
py -3 -c "import sys" >nul 2>nul && set "PY=py -3" && goto :eof
python -c "import sys" >nul 2>nul && set "PY=python" && goto :eof
rem Right after a winget install PATH is not refreshed yet, so look directly.
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set PY="%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
goto :eof

:fail
echo.
echo [ERROR] Setup failed, see the messages above.
pause
exit /b 1
