@echo off
title RAGForge Frontend
cd /d "%~dp0\frontend"
echo Starting RAGForge Frontend (Next.js)...
call npm.cmd run dev
pause
