@echo off
title Second Brain
cd /d "%~dp0"

echo.
echo   ===========================================
echo     🧠 SECOND BRAIN
echo     Starting knowledge graph server...
echo   ===========================================
echo.

python server.py

pause
