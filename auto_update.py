import subprocess, threading, time, sys, os
from pathlib import Path

root = Path(__file__).parent.resolve()

def pull_loop():
    while True:
        time.sleep(60)
        try:
            r = subprocess.run(['git', 'pull'], cwd=root, capture_output=True, text=True, timeout=30)
            if r.stdout.strip():
                print(f"[auto] git pull: {r.stdout.strip()}")
            subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', '-r', 'requirements.txt'],
                         cwd=root, capture_output=True, timeout=30)
        except Exception as e:
            print(f"[auto] pull error: {e}")

threading.Thread(target=pull_loop, daemon=True).start()
os.chdir(root)
sys.path.insert(0, str(root))

import uvicorn, main
uvicorn.run('main:app', host='0.0.0.0', port=8080, reload=True)
