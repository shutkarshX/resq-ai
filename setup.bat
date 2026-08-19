@echo off
setlocal

echo ========================================
echo        RESQ-AI Setup
echo ========================================
echo.

echo [1/4] Creating backend virtual environment...
cd /d "%~dp0backend"

if not exist ".venv\Scripts\python.exe" (
    python -m venv .venv
)

echo [2/4] Installing backend dependencies...
".venv\Scripts\python.exe" -m pip install -r requirements.txt

if not exist ".env" (
    copy ".env.example" ".env" >nul
)

echo [3/4] Seeding demo database...
".venv\Scripts\python.exe" seed.py

echo [4/4] Installing frontend dependencies...
cd /d "%~dp0frontend"
call npm.cmd install

if not exist ".env" (
    copy ".env.example" ".env" >nul
)

echo.
echo ========================================
echo       RESQ-AI setup complete!
echo ========================================
echo.
echo Run "run.bat" to start the application.
echo.

pause