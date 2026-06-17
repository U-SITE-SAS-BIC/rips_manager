@echo off
taskkill /f /im pythonw.exe 2>nul
taskkill /f /im python.exe 2>nul
echo Servidor detenido.
timeout /t 2 /nobreak >nul
exit
