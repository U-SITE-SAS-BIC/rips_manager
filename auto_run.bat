@echo off
chcp 65001 >nul
title RIPS Manager - Auto Update

:: ---- 1. Verificar Python ----
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo Descargando Python 3.12...
    powershell -Command "& {Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.9/python-3.12.9-amd64.exe' -OutFile '%TEMP%\python-installer.exe'}"
    echo Instalando Python (esperar 1-2 min)...
    start /wait "" "%TEMP%\python-installer.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0
    echo Python instalado. Cerra y abri PowerShell de nuevo.
    pause
    exit /b
)

:: ---- 2. Actualizar e instalar deps ----
echo Pull inicial...
git pull
python -m pip install -q -r requirements.txt

:: ---- 3. Arrancar ----
echo.
echo ==========================================
echo  Servidor: http://localhost:8080
echo  Auto-update cada 60 segundos
echo  Cerra esta ventana para detener
echo ==========================================
python auto_update.py
