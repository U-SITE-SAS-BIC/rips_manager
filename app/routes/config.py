from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from app.database import get_connection
from app.auth import get_current_user

router = APIRouter(prefix="/config", tags=["config"])

DEFAULT_KEYS = [
    ("firebird_host", "localhost"),
    ("firebird_port", "3050"),
    ("firebird_database", "/path/to/database.fdb"),
    ("firebird_user", "SYSDBA"),
    ("firebird_password", "masterkey"),
    ("api_url", "https://api.example.com/rips"),
    ("api_method", "POST"),
    ("api_key", ""),
    ("api_timeout", "30"),
    ("num_documento_obligado", ""),
    ("cod_prestador", ""),
]


def ensure_defaults():
    conn = get_connection()
    for key, default in DEFAULT_KEYS:
        exists = conn.execute("SELECT id FROM config WHERE key = ?", (key,)).fetchone()
        if not exists:
            conn.execute("INSERT INTO config (key, value) VALUES (?, ?)", (key, default))
    conn.commit()
    conn.close()


@router.get("")
async def config_page(request: Request, user: dict = Depends(get_current_user)):
    conn = get_connection()
    configs = conn.execute("SELECT * FROM config ORDER BY key").fetchall()
    conn.close()
    return request.app.state.templates.TemplateResponse("config.html", {
        "request": request, "user": user, "configs": configs
    })


@router.post("/save")
async def config_save(request: Request, user: dict = Depends(get_current_user)):
    form = await request.form()
    conn = get_connection()
    for key, value in form.multi_items():
        if key.startswith("config_"):
            real_key = key.replace("config_", "", 1)
            conn.execute(
                "UPDATE config SET value = ? WHERE key = ?",
                (value, real_key)
            )
    conn.commit()
    conn.close()
    return RedirectResponse("/config", status_code=302)
