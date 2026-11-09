@echo off
title SkillBridge - Frontend (React + Vite)
echo ========================================================
echo Starting SkillBridge Frontend (Vite)...
echo ========================================================
set "PATH=%LOCALAPPDATA%\node-portable\node-v20.18.0-win-x64;%PATH%"
cd /d "%~dp0frontend"
call npm run dev
pause
