@echo off
chcp 65001 >nul
cd /d "%~dp0"

:: Verificar Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo Descargando Python...
    powershell -Command "& {Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.9/python-3.12.9-amd64.exe' -OutFile '%TEMP%\python-installer.exe'}"
    start /wait "" "%TEMP%\python-installer.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0
    echo Python instalado. Ejecuta de nuevo el .bat
    pause
    exit /b
)

:: Instalar dependencias
python -m pip install -q -r requirements.txt

:: Matar instancia anterior
taskkill /f /im python.exe 2>nul

:: Iniciar minimizado
start /min python main.py

echo ==========================================
echo  RIPS Manager iniciado (minimizado)
echo  http://localhost:8080
echo  Para detener: doble clic en stop.bat
echo ==========================================
timeout /t 3 /nobreak >nul
exit
