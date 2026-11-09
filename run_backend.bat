@echo off
title SkillBridge - Backend Server
echo ========================================================
echo Starting SkillBridge Backend (FastAPI)...
echo ========================================================
cd /d "%~dp0backend"
call .venv\Scripts\activate.bat
python run.py
pause
