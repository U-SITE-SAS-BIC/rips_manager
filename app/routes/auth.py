from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from app.database import get_connection
from app.auth import hash_password, verify_password, create_token, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login")
async def login_page(request: Request):
    return request.app.state.templates.TemplateResponse("login.html", {"request": request})


@router.get("/register")
async def register_page(request: Request):
    return request.app.state.templates.TemplateResponse("register.html", {"request": request})


@router.post("/register")
async def register(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
):
    if password != confirm_password:
        return request.app.state.templates.TemplateResponse("register.html", {
            "request": request, "error": "Las contraseñas no coinciden"
        })

    conn = get_connection()
    try:
        existing = conn.execute(
            "SELECT id FROM users WHERE username = ? OR email = ?",
            (username, email)
        ).fetchone()
        if existing:
            return request.app.state.templates.TemplateResponse("register.html", {
                "request": request, "error": "Usuario o email ya registrado"
            })

        conn.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, hash_password(password))
        )
        conn.commit()
        return RedirectResponse("/auth/login", status_code=302)
    finally:
        conn.close()


@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    conn = get_connection()
    try:
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        if not user or not verify_password(password, user["password_hash"]):
            return request.app.state.templates.TemplateResponse("login.html", {
                "request": request, "error": "Usuario o contraseña incorrectos"
            })

        token = create_token(user["id"], user["username"])
        resp = RedirectResponse("/dashboard", status_code=302)
        resp.set_cookie(key="token", value=token, httponly=True, max_age=43200)
        return resp
    finally:
        conn.close()


@router.get("/logout")
async def logout():
    resp = RedirectResponse("/auth/login", status_code=302)
    resp.delete_cookie("token")
    return resp


@router.post("/api/login")
async def api_login(username: str = Form(...), password: str = Form(...)):
    conn = get_connection()
    try:
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        if not user or not verify_password(password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        token = create_token(user["id"], user["username"])
        return {"access_token": token, "token_type": "bearer"}
    finally:
        conn.close()
