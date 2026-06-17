@echo off
chcp 65001 >nul
title RIPS Manager - Auto Update

:: ---- 1. Asegurar Python portable ----
if not exist python\python.exe (
    echo Descargando Python portable...
    powershell -Command "& {Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.9/python-3.12.9-embed-amd64.zip' -OutFile 'python.zip'}"
    powershell -Command "& {Expand-Archive -Path 'python.zip' -DestinationPath 'python' -Force}"
    del python.zip
    set PTH_FILE=%~dp0python\python312._pth
    powershell -Command "& {(Get-Content '%PTH_FILE%') -replace '#import site','import site' | Set-Content '%PTH_FILE%'}"
    python\python.exe -c "import urllib.request; exec(urllib.request.urlopen('https://bootstrap.pypa.io/get-pip.py').read())"
)

:: ---- 2. Pull inicial ----
echo [%date% %time%] Pull inicial...
git pull
python\python.exe -m pip install -q -r requirements.txt 2>nul

:: ---- 3. Arrancar con auto-pull cada 60s ----
echo.
echo ==========================================
echo  Servidor: http://localhost:8080
echo  Auto-update cada 60 segundos
echo  Cerra esta ventana para detener
echo ==========================================

python\python.exe auto_update.py
