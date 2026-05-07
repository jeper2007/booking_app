@echo off
title LuxStay — Hotel Booking App
color 0A
echo.
echo  ============================================
echo   LuxStay Hotel Booking System
echo   Starting server...
echo  ============================================
echo.

cd /d "%~dp0"

REM Try python first, fall back to py launcher
where python >nul 2>&1
if %errorlevel%==0 (
    start "" python app.py
) else (
    where py >nul 2>&1
    if %errorlevel%==0 (
        start "" py app.py
    ) else (
        echo ERROR: Python not found. Please install Python.
        pause
        exit /b 1
    )
)

echo  Server is starting... opening browser in 2 seconds.
timeout /t 2 /nobreak >nul
start "" "http://127.0.0.1:5000"
echo  Done! LuxStay is running at http://127.0.0.1:5000
echo  Close this window to stop the server.
pause
