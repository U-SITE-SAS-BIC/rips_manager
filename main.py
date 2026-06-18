import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
import uvicorn

from app.database import init_db
from app.auth import decode_token

app = FastAPI(title="RIPS Manager", version="1.0.0")

templates = Jinja2Templates(
    directory=os.path.join(os.path.dirname(__file__), "app", "templates")
)
app.state.templates = templates


def get_user_from_request(request: Request):
    token = request.cookies.get("token")
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
    if token:
        decoded = decode_token(token)
        if decoded:
            return decoded
        print(f"  [AUTH] Invalid token: {token[:30]}...", flush=True)
    return None


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if request.url.path.startswith("/auth") or request.url.path.startswith("/static"):
        return await call_next(request)

    user = get_user_from_request(request)
    print(f"  [AUTH] path={request.url.path} user={user['username'] if user else None}", flush=True)
    if not user:
        if request.url.path.startswith("/api/"):
            from fastapi.responses import JSONResponse
            return JSONResponse({"detail": "Not authenticated"}, status_code=401)
        return RedirectResponse(url="/auth/login")

    request.state.user = user
    return await call_next(request)


@app.on_event("startup")
async def startup():
    init_db()
    from app.routes.config import ensure_defaults as config_defaults
    from app.routes.queries import ensure_defaults as query_defaults
    config_defaults()
    query_defaults()


@app.get("/")
async def root():
    return RedirectResponse(url="/dashboard")


from app.routes import auth, dashboard, config, queries, terceros, transaccion, logs, automation

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(config.router)
app.include_router(queries.router)
app.include_router(terceros.router)
app.include_router(transaccion.router)
app.include_router(logs.router)
app.include_router(automation.router)


if __name__ == "__main__":
    import socket
    hostname = socket.gethostname()
    try:
        lan_ip = socket.gethostbyname(hostname)
    except Exception:
        lan_ip = "0.0.0.0"
    print(f"  Local: http://localhost:8080")
    print(f"  Red:   http://{lan_ip}:8080")
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=False)
