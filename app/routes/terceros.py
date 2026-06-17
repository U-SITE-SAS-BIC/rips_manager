from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from app.database import get_connection
from app.auth import get_current_user
from app.services.firebird_service import FirebirdService
from app.services.json_generator import generar_terceros

router = APIRouter(prefix="/terceros", tags=["terceros"])


@router.get("")
async def terceros_page(request: Request, user: dict = Depends(get_current_user)):
    conn = get_connection()
    envios = conn.execute("""
        SELECT * FROM envios WHERE tipo = 'terceros'
        ORDER BY created_at DESC LIMIT 20
    """).fetchall()
    queries = conn.execute(
        "SELECT * FROM queries WHERE query_type = 'terceros' ORDER BY name"
    ).fetchall()
    configs = {row["key"]: row["value"] for row in conn.execute("SELECT * FROM config").fetchall()}
    conn.close()

    return request.app.state.templates.TemplateResponse("terceros.html", {
        "request": request, "user": user,
        "envios": envios, "queries": queries,
        "configs": configs,
        "firebird_host": configs.get("firebird_host", "localhost"),
        "firebird_port": configs.get("firebird_port", "3050"),
        "firebird_database": configs.get("firebird_database", ""),
    })


@router.post("/test-connection")
async def test_connection(
    request: Request,
    user: dict = Depends(get_current_user),
    host: str = Form(...),
    port: int = Form(...),
    database: str = Form(...),
    fb_user: str = Form(...),
    fb_password: str = Form(...),
):
    fb = FirebirdService()
    success, msg = fb.connect(host, port, database, fb_user, fb_password)
    if success:
        fb.disconnect()
    return JSONResponse({"success": success, "message": msg})


@router.post("/preview")
async def preview_query(
    request: Request,
    user: dict = Depends(get_current_user),
    query_id: int = Form(...),
    doc_num: str = Form(""),
):
    conn = get_connection()
    q = conn.execute("SELECT * FROM queries WHERE id = ?", (query_id,)).fetchone()
    configs = {row["key"]: row["value"] for row in conn.execute("SELECT * FROM config").fetchall()}
    conn.close()

    if not q:
        return JSONResponse({"success": False, "message": "Consulta no encontrada"})

    fb = FirebirdService()
    fb_success, fb_msg = fb.connect(
        configs.get("firebird_host", "localhost"),
        int(configs.get("firebird_port", 3050)),
        configs.get("firebird_database", ""),
        configs.get("firebird_user", "SYSDBA"),
        configs.get("firebird_password", "masterkey"),
    )
    if not fb_success:
        return JSONResponse({"success": False, "message": f"Error Firebird: {fb_msg}"})

    params = {}
    if ":doc_num" in q["query_text"] and doc_num:
        params["doc_num"] = doc_num
    if ":fecha_ini" in q["query_text"]:
        params["fecha_ini"] = "1900-01-01"
        params["fecha_fin"] = "2100-12-31"
    if ":factura" in q["query_text"]:
        params["factura"] = doc_num if doc_num else ""

    success, error, rows = fb.execute_query(q["query_text"], params if params else None)
    fb.disconnect()

    if not success:
        return JSONResponse({"success": False, "message": error})

    json_result = None
    if rows:
        json_result = generar_terceros(rows[0])

    return JSONResponse({
        "success": True,
        "rows_count": len(rows),
        "columns": list(rows[0].keys()) if rows else [],
        "preview": rows[:5],
        "generated_json": json_result,
    })


@router.post("/send")
async def send_terceros(
    request: Request,
    user: dict = Depends(get_current_user),
    query_id: int = Form(...),
    doc_num: str = Form(""),
):
    import json
    import httpx
    from datetime import datetime

    conn = get_connection()
    q = conn.execute("SELECT * FROM queries WHERE id = ?", (query_id,)).fetchone()
    configs = {row["key"]: row["value"] for row in conn.execute("SELECT * FROM config").fetchall()}
    conn.close()

    if not q:
        return JSONResponse({"success": False, "message": "Consulta no encontrada"})

    fb = FirebirdService()
    fb_success, fb_msg = fb.connect(
        configs.get("firebird_host", "localhost"),
        int(configs.get("firebird_port", 3050)),
        configs.get("firebird_database", ""),
        configs.get("firebird_user", "SYSDBA"),
        configs.get("firebird_password", "masterkey"),
    )
    if not fb_success:
        return JSONResponse({"success": False, "message": f"Error Firebird: {fb_msg}"})

    params = {}
    if ":doc_num" in q["query_text"]:
        params["doc_num"] = doc_num or configs.get("doc_num_default", "")

    success, error, rows = fb.execute_query(q["query_text"], params if params else None)
    fb.disconnect()

    if not success:
        return JSONResponse({"success": False, "message": error})

    if not rows:
        return JSONResponse({"success": False, "message": "No se encontraron datos"})

    # Generar JSON terceros
    tercero_json = generar_terceros(rows[0])

    # Enviar a API
    api_url = configs.get("api_url", "")
    api_key = configs.get("api_key", "")
    api_method = configs.get("api_method", "POST")

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        async with httpx.AsyncClient(timeout=int(configs.get("api_timeout", 30))) as client:
            if api_method == "POST":
                resp = await client.post(api_url + "/terceros", json=tercero_json, headers=headers)
            else:
                resp = await client.put(api_url + "/terceros", json=tercero_json, headers=headers)

        result = resp.status_code, resp.is_success, resp.text
    except Exception as e:
        result = (0, False, str(e))

    # Guardar log
    conn = get_connection()
    conn.execute("""
        INSERT INTO envios (user_id, tipo, status, json_enviado, respuesta_api, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        user["user_id"], "terceros",
        "success" if result[1] else "error",
        json.dumps(tercero_json, indent=2, ensure_ascii=False),
        str(result[2])[:1000],
        datetime.now().isoformat(),
    ))
    conn.commit()
    conn.close()

    return JSONResponse({
        "success": result[1],
        "status_code": result[0],
        "message": "Envío exitoso" if result[1] else f"Error: {result[2]}",
        "cuv": result[2][:200] if result[1] else None,
    })
