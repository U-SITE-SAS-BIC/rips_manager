import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, Request, Depends
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.database import init_db
from app.auth import decode_token

app = FastAPI(title="RIPS Manager", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(
    directory=os.path.join(os.path.dirname(__file__), "app", "templates")
)
app.state.templates = templates


def get_user_from_request(request: Request):
    cookies = dict(request.cookies)
    token = cookies.get("token")
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
    public_paths = ["/auth/login", "/auth/register", "/auth/api/login"]
    if request.url.path in public_paths or request.url.path.startswith("/static"):
        return await call_next(request)

    if request.url.path.startswith("/auth"):
        return await call_next(request)

    user = get_user_from_request(request)
    print(f"  [AUTH] path={request.url.path} user={user['username'] if user else None} cookies={dict(request.cookies)}", flush=True)
    if not user:
        if request.url.path.startswith("/api/"):
            from fastapi.responses import JSONResponse
            print(f"  [AUTH] -> 401 JSON for /api/ path", flush=True)
            return JSONResponse({"detail": "Not authenticated"}, status_code=401)
        print(f"  [AUTH] -> 307 redirect to /auth/login", flush=True)
        return RedirectResponse(url="/auth/login")

    request.state.user = user
    return await call_next(request)


@app.on_event("startup")
async def startup():
    init_db()


@app.get("/")
async def root():
    return RedirectResponse(url="/dashboard")


# Register routes
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
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
