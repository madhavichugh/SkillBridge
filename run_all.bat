@echo off
title SkillBridge Launcher
echo ========================================================
echo Launching SkillBridge Backend and Frontend...
echo ========================================================
start "SkillBridge Backend" cmd /k "%~dp0run_backend.bat"
timeout /t 3 /nobreak >nul
start "SkillBridge Frontend" cmd /k "%~dp0run_frontend.bat"
echo SkillBridge is starting!
echo Backend:  http://127.0.0.1:8000
echo Frontend: http://localhost:5173
pause
