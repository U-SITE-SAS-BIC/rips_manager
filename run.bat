@echo off
chcp 65001 >nul

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

:: Matar instancia anterior si existe
taskkill /f /im python.exe 2>nul
taskkill /f /im pythonw.exe 2>nul

:: Iniciar sin ventana
start /b pythonw main.py

echo ==========================================
echo  RIPS Manager iniciado en segundo plano
echo  http://localhost:8080
echo ==========================================
timeout /t 5 /nobreak >nul
exit
