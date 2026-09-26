@echo off
title AegisFlow Setup
color 0B

echo.
echo ============================================================
echo   🛡️  AegisFlow — Setup & Installation
echo ============================================================
echo.

:: Check Python version
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Install Python 3.11+ first.
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✓ Python found
echo.

:: Check MongoDB
echo Checking MongoDB connection...
python -c "from pymongo import MongoClient; MongoClient('mongodb://localhost:27017', serverSelectionTimeoutMS=2000).admin.command('ping'); print('✓ MongoDB is running')" 2>nul
if errorlevel 1 (
    echo ⚠️  MongoDB not found on localhost:27017
    echo Start MongoDB Compass or run: mongod
    echo (Continuing anyway - you'll need MongoDB before running the app)
    echo.
)

:: Create venv
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo ✓ Virtual environment created
    echo.
)

:: Activate venv
call venv\Scripts\activate.bat

:: Install dependencies
echo Installing dependencies...
echo (This may take 1-2 minutes)
pip install --upgrade pip setuptools wheel >nul 2>&1
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo ❌ Installation failed!
    echo Try running manually:
    echo   venv\Scripts\activate
    echo   pip install -r requirements.txt
    pause
    exit /b 1
)

echo ✓ Dependencies installed
echo.

:: Get Gemini API key
echo.
echo ============================================================
echo   🔑 Gemini API Key Setup
echo ============================================================
echo.
echo Get your FREE API key at:
echo https://aistudio.google.com/app/apikey
echo.
echo Then edit the .env file and add:
echo GEMINI_API_KEY=your_key_here
echo.

:: Create .env if doesn't exist
if not exist ".env" (
    echo Creating .env file...
    (
        echo # AegisFlow Environment Configuration
        echo MONGO_URI=mongodb://localhost:27017/aegisflow
        echo DB_NAME=aegisflow
        echo GEMINI_API_KEY=your_gemini_api_key_here
        echo SECRET_KEY=aegisflow-secret-2024-change-this
        echo ALGORITHM=HS256
        echo ACCESS_TOKEN_EXPIRE_MINUTES=1440
        echo APP_ENV=development
        echo APP_PORT=8000
        echo FRONTEND_PORT=3000
        echo CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
    ) > .env
    echo ✓ .env file created
    echo.
)

echo ============================================================
echo   ✅ Setup Complete!
echo ============================================================
echo.
echo Next steps:
echo.
echo 1. Edit .env file and add your Gemini API key:
echo    GEMINI_API_KEY=your_key_from_aistudio.google.com
echo.
echo 2. Make sure MongoDB is running (Compass or mongod)
echo.
echo 3. Double-click START.bat to run AegisFlow
echo.
echo ============================================================
echo.

pause
