@echo off
title RAGForge Backend
cd /d "%~dp0\backend"
echo Starting RAGForge Backend (FastAPI)...
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
pause
