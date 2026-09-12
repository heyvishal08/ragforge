@echo off
title RAGForge Demo Seeder
cd /d "%~dp0\backend"
echo Seeding Demo Knowledge Base with sample reports...
python -m app.scripts.seed_demo
pause
