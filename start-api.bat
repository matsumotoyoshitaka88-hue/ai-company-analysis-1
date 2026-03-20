@echo off
cd /d "%~dp0apps\api"
.venv\Scripts\uvicorn app.main:app --reload --port 8000
