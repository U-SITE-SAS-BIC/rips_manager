@echo off
chcp 65001 >nul
title RIPS Manager - Iniciando...

:: Verificar si ya existe Python portable
if exist python\python.exe goto :start

echo ==========================================
echo  Descargando Python portable...
echo ==========================================
echo.

:: Descargar Python embeddable (64-bit)
powershell -Command "& {Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.9/python-3.12.9-embed-amd64.zip' -OutFile 'python.zip'}"

if not exist python.zip (
    echo ERROR: No se pudo descargar Python
    pause
    exit /b
)

echo.
echo Extrayendo...
powershell -Command "& {Expand-Archive -Path 'python.zip' -DestinationPath 'python' -Force}"
del python.zip

:: Habilitar pip (descomentar línea en el archivo de configuración)
set PYTHON_EXE=%~dp0python\python.exe
set PTH_FILE=%~dp0python\python312._pth
powershell -Command "& {(Get-Content '%PTH_FILE%') -replace '#import site','import site' | Set-Content '%PTH_FILE%'}"

:: Instalar pip
echo.
echo Instalando pip...
%PYTHON_EXE% -c "import urllib.request; exec(urllib.request.urlopen('https://bootstrap.pypa.io/get-pip.py').read())"

:start
echo.
echo Instalando dependencias...
python\python.exe -m pip install -q -r requirements.txt 2>nul

echo.
echo ==========================================
echo  Servidor iniciado en http://localhost:8080
echo  Presiona Ctrl+C para detener
echo ==========================================
python\python.exe main.py
pause
