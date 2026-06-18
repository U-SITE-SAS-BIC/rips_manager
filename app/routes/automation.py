import json as json_lib
import httpx
from datetime import datetime
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import JSONResponse
from app.database import get_connection
from app.auth import get_current_user
from app.services.firebird_service import get_firebird_from_config
from app.services.json_generator import generar_terceros, generar_transaccion, agrupar_por_factura

router = APIRouter(prefix="/automation", tags=["automation"])


@router.get("")
async def automation_page(request: Request, user: dict = Depends(get_current_user)):
    conn = get_connection()
    queries = conn.execute("SELECT * FROM queries ORDER BY query_type, name").fetchall()
    configs = {row["key"]: row["value"] for row in conn.execute("SELECT * FROM config").fetchall()}
    conn.close()

    return request.app.state.templates.TemplateResponse("automation.html", {
        "request": request, "user": user,
        "queries": queries, "configs": configs,
    })


@router.post("/run")
async def run_automation(
    request: Request,
    user: dict = Depends(get_current_user),
    query_terceros_id: int = Form(...),
    query_transaccion_id: int = Form(...),
    fecha_inicio: str = Form(...),
    fecha_fin: str = Form(...),
    factura: str = Form(""),
):
    conn = get_connection()
    q_terceros = conn.execute("SELECT * FROM queries WHERE id = ?", (query_terceros_id,)).fetchone()
    q_trans = conn.execute("SELECT * FROM queries WHERE id = ?", (query_transaccion_id,)).fetchone()
    configs = {row["key"]: row["value"] for row in conn.execute("SELECT * FROM config").fetchall()}
    conn.close()

    if not q_terceros or not q_trans:
        return JSONResponse({"success": False, "message": "Consultas no encontradas"})

    fb, fb_ok, fb_msg = get_firebird_from_config(configs)
    if not fb_ok:
        return JSONResponse({"success": False, "message": f"Error Firebird: {fb_msg}"})

    api_url = configs.get("api_url", "")
    api_key = configs.get("api_key", "")
    api_method = configs.get("api_method", "POST")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    resultado = {"paso1_terceros": {"status": "pendiente"}, "paso2_transaccion": {"status": "pendiente"}}

    # ---------------------------------------------------------------
    # PASO 1: Enviar TERCEROS
    # ---------------------------------------------------------------
    params = {"fecha_ini": fecha_inicio, "fecha_fin": fecha_fin}
    if ":factura" in q_terceros["query_text"] and factura:
        params["factura"] = factura
    if ":doc_num" in q_terceros["query_text"]:
        params["doc_num"] = ""

    success, error, rows = fb.execute_query(
        q_terceros["query_text"],
        params if ":fecha_ini" in q_terceros["query_text"] else None
    )

    if not success:
        resultado["paso1_terceros"] = {"status": "error", "message": error}
    elif not rows:
        resultado["paso1_terceros"] = {"status": "error", "message": "No hay pacientes para enviar"}
    else:
        terceros_enviados = 0
        terceros_errores = 0
        pacientes_enviados = []

        async with httpx.AsyncClient(timeout=int(configs.get("api_timeout", 30))) as client:
            for row in rows:
                tercero_json = generar_terceros(row)
                doc_id = tercero_json["numDocumentoIdentificacion"]
                if doc_id in pacientes_enviados:
                    continue
                pacientes_enviados.append(doc_id)

                resp_ok = False
                resp_text = ""
                try:
                    if api_method == "POST":
                        resp = await client.post(api_url + "/terceros", json=tercero_json, headers=headers)
                    else:
                        resp = await client.put(api_url + "/terceros", json=tercero_json, headers=headers)
                    resp_ok = resp.is_success
                    resp_text = resp.text[:1000]
                    if resp_ok:
                        terceros_enviados += 1
                    else:
                        terceros_errores += 1
                except Exception as e:
                    terceros_errores += 1
                    resp_text = str(e)

                conn = get_connection()
                conn.execute("""
                    INSERT INTO envios (user_id, tipo, factura, status, json_enviado, respuesta_api, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    user["user_id"], "terceros", factura or "AUTO",
                    "success" if resp_ok else "error",
                    json_lib.dumps(tercero_json, indent=2, ensure_ascii=False),
                    resp_text,
                    datetime.now().isoformat(),
                ))
                conn.commit()
                conn.close()

        resultado["paso1_terceros"] = {
            "status": "success" if terceros_errores == 0 else "partial",
            "enviados": terceros_enviados,
            "errores": terceros_errores,
        }

    # ---------------------------------------------------------------
    # PASO 2: Enviar TRANSACCION
    # ---------------------------------------------------------------
    params = {"fecha_ini": fecha_inicio, "fecha_fin": fecha_fin}
    if ":factura" in q_trans["query_text"] and factura:
        params["factura"] = factura

    success, error, rows = fb.execute_query(q_trans["query_text"], params)

    if not success:
        resultado["paso2_transaccion"] = {"status": "error", "message": error}
    elif not rows:
        resultado["paso2_transaccion"] = {"status": "error", "message": "No hay servicios para enviar"}
    else:
        grupos = agrupar_por_factura(rows, factura)
        trans_enviados = 0
        trans_errores = 0

        async with httpx.AsyncClient(timeout=int(configs.get("api_timeout", 30))) as client:
            for (fact, doc_key), grupo in grupos.items():
                paciente_data = {"tipoDocumentoIdentificacion": doc_key[0], "numDocumentoIdentificacion": doc_key[1]}
                trans_json = generar_transaccion(
                    fact, configs.get("num_documento_obligado", ""),
                    paciente_data, grupo["procedimientos"],
                )

                status_ok = False
                resp_text = ""
                try:
                    if api_method == "POST":
                        resp = await client.post(api_url + "/transaccion", json=trans_json, headers=headers)
                    else:
                        resp = await client.put(api_url + "/transaccion", json=trans_json, headers=headers)
                    status_ok = resp.is_success
                    resp_text = resp.text[:1000]
                except Exception as e:
                    resp_text = str(e)

                if status_ok:
                    trans_enviados += 1
                else:
                    trans_errores += 1

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
                    resp_text,
                    datetime.now().isoformat(),
                ))
                conn.commit()
                conn.close()

        resultado["paso2_transaccion"] = {
            "status": "success" if trans_errores == 0 else "partial",
            "enviados": trans_enviados,
            "errores": trans_errores,
        }

    fb.disconnect()
    return JSONResponse({"success": True, "resultado": resultado})
