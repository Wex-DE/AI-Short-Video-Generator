@echo off
title WexAuto AI Studio
cd /d "%~dp0"

echo ========================================================
echo                 Starting WexAuto Studio...
echo ========================================================

rem Check if Python virtual environment is healthy on this PC
set "ENV_HEALTHY=0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -c "import streamlit" >nul 2>nul
    if not errorlevel 1 set "ENV_HEALTHY=1"
)

rem If missing, moved from another PC, or broken, auto-repair
if "%ENV_HEALTHY%"=="0" (
    echo [Info] First-time setup or new PC detected. Configuring environment...
    
    set "UV_CMD="
    where uv >nul 2>nul
    if not errorlevel 1 (
        set "UV_CMD=uv"
    ) else if exist "%USERPROFILE%\.local\bin\uv.exe" (
        set "UV_CMD=%USERPROFILE%\.local\bin\uv.exe"
        set "PATH=%USERPROFILE%\.local\bin;%PATH%"
    ) else if exist "%USERPROFILE%\.cargo\bin\uv.exe" (
        set "UV_CMD=%USERPROFILE%\.cargo\bin\uv.exe"
        set "PATH=%USERPROFILE%\.cargo\bin;%PATH%"
    ) else if exist "%LOCALAPPDATA%\uv\uv.exe" (
        set "UV_CMD=%LOCALAPPDATA%\uv\uv.exe"
        set "PATH=%LOCALAPPDATA%\uv;%PATH%"
    ) else if exist "%APPDATA%\uv\uv.exe" (
        set "UV_CMD=%APPDATA%\uv\uv.exe"
        set "PATH=%APPDATA%\uv;%PATH%"
    ) else if exist "%LOCALAPPDATA%\Programs\uv\uv.exe" (
        set "UV_CMD=%LOCALAPPDATA%\Programs\uv\uv.exe"
        set "PATH=%LOCALAPPDATA%\Programs\uv;%PATH%"
    ) else (
        echo [Info] Installing runtime manager (uv)...
        powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 -bor [Net.SecurityProtocolType]::Tls13; irm https://astral.sh/uv/install.ps1 | iex"
        if exist "%USERPROFILE%\.local\bin\uv.exe" (
            set "UV_CMD=%USERPROFILE%\.local\bin\uv.exe"
            set "PATH=%USERPROFILE%\.local\bin;%PATH%"
        ) else if exist "%USERPROFILE%\.cargo\bin\uv.exe" (
            set "UV_CMD=%USERPROFILE%\.cargo\bin\uv.exe"
            set "PATH=%USERPROFILE%\.cargo\bin;%PATH%"
        ) else if exist "%LOCALAPPDATA%\uv\uv.exe" (
            set "UV_CMD=%LOCALAPPDATA%\uv\uv.exe"
            set "PATH=%LOCALAPPDATA%\uv;%PATH%"
        ) else if exist "%APPDATA%\uv\uv.exe" (
            set "UV_CMD=%APPDATA%\uv\uv.exe"
            set "PATH=%APPDATA%\uv;%PATH%"
        ) else if exist "%LOCALAPPDATA%\Programs\uv\uv.exe" (
            set "UV_CMD=%LOCALAPPDATA%\Programs\uv\uv.exe"
            set "PATH=%LOCALAPPDATA%\Programs\uv;%PATH%"
        )
    )
    
    if defined UV_CMD (
        echo [Info] Syncing Python dependencies (one-time auto-setup)...
        "%UV_CMD%" sync
    ) else (
        echo [Warning] Automatic setup manager not found. Trying to proceed...
    )
)

call webui.bat
if errorlevel 1 (
    echo.
    echo [Error] Failed to launch WexAuto.
    pause
)
