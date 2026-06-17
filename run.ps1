Set-Location $PSScriptRoot

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "Descargando Python 3.12..."
    Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.12.9/python-3.12.9-amd64.exe" -OutFile "$env:TEMP\python-installer.exe"
    Write-Host "Instalando Python..."
    Start-Process -Wait -FilePath "$env:TEMP\python-installer.exe" -ArgumentList "/quiet InstallAllUsers=0 PrependPath=1 Include_test=0"
    Write-Host "Python instalado. Cerra y abri PowerShell de nuevo."
    Read-Host "Enter para salir"
    exit
}

Write-Host "Instalando dependencias..."
python -m pip install -q -r requirements.txt

$ip = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -like "192.*" -or $_.IPAddress -like "10.*" -or $_.IPAddress -like "172.*"} | Select-Object -First 1).IPAddress
Write-Host "`n=========================================="
Write-Host " Local: http://localhost:8080"
if ($ip) { Write-Host " Red:   http://$($ip):8080" }
Write-Host " Presiona Ctrl+C para detener"
Write-Host "==========================================`n"

python main.py
