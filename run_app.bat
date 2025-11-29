@echo off
echo ============================================================
echo Smart Task Analyzer - Windows Launcher
echo ============================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

echo Starting Smart Task Analyzer...
echo.
echo Backend API: http://127.0.0.1:8000
echo Frontend UI: http://localhost:8080
echo.
echo Instructions:
echo 1. Two command windows will open
echo 2. Wait for both servers to start
echo 3. Browser will open automatically
echo 4. Close both windows to stop servers
echo.
echo ============================================================
echo.

REM Start backend in new window
start "Django Backend" python start_backend.py

REM Wait a moment for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend in new window
start "Frontend Server" python start_frontend.py

echo Both servers are starting in separate windows...
echo Close this window or press any key to exit.
pause
