@echo off
setlocal

echo ========================================
echo        Starting RESQ-AI
echo ========================================
echo.

start "RESQ-AI Backend" cmd /k "cd /d "%~dp0backend" && .venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000"

timeout /t 3 /nobreak >nul

start "RESQ-AI Frontend" cmd /k "cd /d "%~dp0frontend" && npm.cmd run dev"

echo.
echo ========================================
echo RESQ-AI is starting...
echo ========================================
echo.
echo Backend:  http://127.0.0.1:8000
echo Frontend: http://localhost:5173
echo.
echo Two terminal windows have been opened.
echo Close those windows to stop RESQ-AI.
echo.

pause