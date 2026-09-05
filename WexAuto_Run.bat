@echo off
title WexAuto AI Studio
cd /d "%~dp0"

echo ========================================================
echo                 Starting WexAuto Studio...
echo ========================================================

rem Check if environment exists or if uv is available
if not exist ".venv\Scripts\python.exe" (
    echo [Info] First-time setup detected. Configuring environment...
    where uv >nul 2>nul
    if errorlevel 1 (
        echo [Info] Installing portable runtime manager...
        powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
    )
    call uv sync
)

call webui.bat
if errorlevel 1 (
    echo.
    echo [Error] Failed to launch WexAuto.
    pause
)
