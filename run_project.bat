@echo off
title GramSetu AI - Local Community Issue Management System
echo =====================================================================
echo  Starting GramSetu AI: Local Community Issue Management System
echo  Accessible on Localhost AND on Local Network / Wi-Fi
echo =====================================================================

cd /d "%~dp0backend"
echo [1/2] Launching FastAPI Backend on 0.0.0.0:8000 ...
start "GramSetu Backend" cmd /k "python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 3 /nobreak >nul

cd /d "%~dp0frontend"
echo [2/2] Launching React Vite Frontend on 0.0.0.0:5173 ...
start "GramSetu Frontend" cmd /k "npm run dev -- --host 0.0.0.0"

echo.
echo =====================================================================
echo  Services launched successfully!
echo.
echo  Your Laptop URL:
echo    http://localhost:5173
echo.
echo  Other Mobile Phones / Laptops on Same Wi-Fi:
echo    http://10.189.65.144:5173
echo.
echo  Backend Swagger Docs:
echo    http://localhost:8000/docs
echo =====================================================================
pause
