@echo off
title AegisFlow Launcher
color 0B

echo.
echo ============================================================
echo   🛡️  AegisFlow — AI DevSecOps Platform
echo ============================================================
echo.

:: Check if venv exists
if not exist "venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv venv
    echo.
    echo Installing dependencies...
    venv\Scripts\pip install -r requirements.txt
    echo.
)

echo Starting Backend on port 8000...
start "AegisFlow Backend" cmd /k "venv\Scripts\activate && python -m uvicorn backend.app:app --reload --port 8000"

timeout /t 3 /nobreak > nul

echo Starting Frontend on port 3000...
start "AegisFlow Frontend" cmd /k "cd frontend && python -m http.server 3000 --bind 127.0.0.1"

timeout /t 2 /nobreak > nul

echo.
echo ============================================================
echo   ✅ AegisFlow is RUNNING!
echo ============================================================
echo.
echo   🌐 Open in browser:
echo   http://127.0.0.1:3000/login.html
echo.
echo   📚 API Docs:
echo   http://127.0.0.1:8000/docs
echo ============================================================
echo.

start "" "http://127.0.0.1:3000/login.html"

pause
