import json as json_lib
import httpx
from datetime import datetime
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import JSONResponse
from app.database import get_connection
from app.auth import get_current_user
from app.services.firebird_service import get_firebird_from_config
from app.services.json_generator import generar_transaccion, agrupar_por_factura

router = APIRouter(prefix="/transaccion", tags=["transaccion"])


@router.get("")
async def transaccion_page(request: Request, user: dict = Depends(get_current_user)):
    conn = get_connection()
    envios = conn.execute("""
        SELECT * FROM envios WHERE tipo = 'transaccion'
        ORDER BY created_at DESC LIMIT 20
    """).fetchall()
    queries = conn.execute(
        "SELECT * FROM queries WHERE query_type = 'transaccion' ORDER BY name"
    ).fetchall()
    configs = {row["key"]: row["value"] for row in conn.execute("SELECT * FROM config").fetchall()}
    conn.close()

    return request.app.state.templates.TemplateResponse("transaccion.html", {
        "request": request, "user": user,
        "envios": envios, "queries": queries,
        "configs": configs,
    })


@router.post("/preview")
async def preview_transaccion(
    request: Request,
    user: dict = Depends(get_current_user),
    query_id: int = Form(...),
    factura: str = Form(""),
    fecha_inicio: str = Form(...),
    fecha_fin: str = Form(...),
):
    conn = get_connection()
    q = conn.execute("SELECT * FROM queries WHERE id = ?", (query_id,)).fetchone()
    configs = {row["key"]: row["value"] for row in conn.execute("SELECT * FROM config").fetchall()}
    conn.close()

    if not q:
        return JSONResponse({"success": False, "message": "Consulta no encontrada"})

    fb, ok, msg = get_firebird_from_config(configs)
    if not ok:
        return JSONResponse({"success": False, "message": f"Error Firebird: {msg}"})

    params = {"fecha_ini": fecha_inicio, "fecha_fin": fecha_fin}
    if ":factura" in q["query_text"] and factura:
        params["factura"] = factura

    success, error, rows = fb.execute_query(q["query_text"], params)
    fb.disconnect()

    if not success:
        return JSONResponse({"success": False, "message": error})

    grupos = agrupar_por_factura(rows, factura)
    json_result = []
    for (fact, doc_key), grupo in grupos.items():
        paciente_data = {"tipoDocumentoIdentificacion": doc_key[0], "numDocumentoIdentificacion": doc_key[1]}
        json_result.append(generar_transaccion(
            fact, configs.get("num_documento_obligado", ""),
            paciente_data, grupo["procedimientos"],
        ))

    return JSONResponse({
        "success": True,
        "rows_count": len(rows),
        "grupos_count": len(grupos),
        "columns": list(rows[0].keys()) if rows else [],
        "preview": rows[:5],
        "generated_json": json_result[0] if json_result else None,
        "total_json": len(json_result),
    })


@router.post("/send")
async def send_transaccion(
    request: Request,
    user: dict = Depends(get_current_user),
    query_id: int = Form(...),
    factura: str = Form(""),
    fecha_inicio: str = Form(...),
    fecha_fin: str = Form(...),
):
    conn = get_connection()
    q = conn.execute("SELECT * FROM queries WHERE id = ?", (query_id,)).fetchone()
    configs = {row["key"]: row["value"] for row in conn.execute("SELECT * FROM config").fetchall()}
    conn.close()

    if not q:
        return JSONResponse({"success": False, "message": "Consulta no encontrada"})

    fb, ok, msg = get_firebird_from_config(configs)
    if not ok:
        return JSONResponse({"success": False, "message": f"Error Firebird: {msg}"})

    params = {"fecha_ini": fecha_inicio, "fecha_fin": fecha_fin}
    if ":factura" in q["query_text"] and factura:
        params["factura"] = factura

    success, error, rows = fb.execute_query(q["query_text"], params)
    fb.disconnect()

    if not success:
        return JSONResponse({"success": False, "message": error})
    if not rows:
        return JSONResponse({"success": False, "message": "No se encontraron datos"})

    grupos = agrupar_por_factura(rows, factura)
    api_url = configs.get("api_url", "")
    api_key = configs.get("api_key", "")
    api_method = configs.get("api_method", "POST")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    total_enviados = 0
    total_errores = 0
    resultados = []

    async with httpx.AsyncClient(timeout=int(configs.get("api_timeout", 30))) as client:
        for (fact, doc_key), grupo in grupos.items():
            paciente_data = {"tipoDocumentoIdentificacion": doc_key[0], "numDocumentoIdentificacion": doc_key[1]}
            trans_json = generar_transaccion(
                fact, configs.get("num_documento_obligado", ""),
                paciente_data, grupo["procedimientos"],
            )

            status_ok = False
            response_text = ""
            try:
                if api_method == "POST":
                    resp = await client.post(api_url + "/transaccion", json=trans_json, headers=headers)
                else:
                    resp = await client.put(api_url + "/transaccion", json=trans_json, headers=headers)
                status_ok = resp.is_success
                response_text = resp.text[:1000]
            except Exception as e:
                response_text = str(e)

            if status_ok:
                total_enviados += 1
            else:
                total_errores += 1

            resultados.append({"factura": fact, "success": status_ok})

            conn = get_connection()
            conn.execute("""
                INSERT INTO envios (user_id, tipo, factura, fecha_inicio, fecha_fin,
                    pacientes_count, servicios_count, status, json_enviado, respuesta_api, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user["user_id"], "transaccion", fact,
                fecha_inicio, fecha_fin,
                1, len(grupo["procedimientos"]),
                "success" if status_ok else "error",
                json_lib.dumps(trans_json, indent=2, ensure_ascii=False)[:5000],
                response_text,
                datetime.now().isoformat(),
            ))
            conn.commit()
            conn.close()

    return JSONResponse({
        "success": total_errores == 0,
        "total_enviados": total_enviados,
        "total_errores": total_errores,
        "resultados": resultados,
        "message": f"Enviados: {total_enviados}, Errores: {total_errores}",
    })
