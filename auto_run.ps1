$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

# Verificar Python
$python = (Get-Command python -ErrorAction SilentlyContinue)
if (-not $python) {
    Write-Host "Descargando Python 3.12..."
    $url = "https://www.python.org/ftp/python/3.12.9/python-3.12.9-amd64.exe"
    $dest = "$env:TEMP\python-installer.exe"
    Invoke-WebRequest -Uri $url -OutFile $dest
    Write-Host "Instalando Python..."
    Start-Process -Wait -FilePath $dest -ArgumentList "/quiet InstallAllUsers=0 PrependPath=1 Include_test=0"
    Write-Host "Python instalado. Cerra y abri PowerShell de nuevo."
    Read-Host "Presiona Enter para salir"
    exit
}

# Pull
Write-Host "Pull inicial..."
git pull
python -m pip install -q -r requirements.txt

Write-Host "`n=========================================="
Write-Host " Servidor: http://localhost:8080"
Write-Host " Auto-update cada 60 segundos"
Write-Host " Cerra esta ventana para detener"
Write-Host "==========================================`n"

python auto_update.py
