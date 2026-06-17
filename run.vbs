Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "powershell -ExecutionPolicy Bypass -NoProfile -Command ""Start-Process python -ArgumentList 'main.py' -WindowStyle Hidden""", 0, False
