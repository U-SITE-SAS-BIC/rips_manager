from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from app.database import get_connection
from app.auth import get_current_user
from app.models import QueryCreate

router = APIRouter(prefix="/queries", tags=["queries"])

QUERY_DEFAULTS = [
    {
        "name": "Terceros - Datos del paciente",
        "query_type": "terceros",
        "query_text": """SELECT
    p.TIPO_DOCUMENTO as tipo_documento,
    p.NUMERO_DOCUMENTO as numero_documento,
    p.PRIMER_NOMBRE as primer_nombre,
    p.SEGUNDO_NOMBRE as segundo_nombre,
    p.PRIMER_APELLIDO as primer_apellido,
    p.SEGUNDO_APELLIDO as segundo_apellido,
    p.FECHA_NACIMIENTO as fecha_nacimiento,
    p.SEXO as cod_sexo,
    p.COD_ENTIDAD as cod_entidad,
    p.TIPO_USUARIO as tipo_usuario,
    p.COD_MUNICIPIO as cod_municipio,
    p.ZONA as cod_zona,
    p.DIRECCION as direccion
FROM USUAHOS p
WHERE p.NUMERO_DOCUMENTO = :doc_num""",
        "description": "Consulta datos maestros del paciente por documento"
    },
    {
        "name": "Procedimientos por factura",
        "query_type": "transaccion",
        "query_text": """SELECT
    s.CODIGO_CUP as cod_procedimiento,
    s.FECHA_ATENCION as fecha_atencion,
    s.COD_DIAGNOSTICO as cod_diagnostico,
    s.FINALIDAD as finalidad,
    s.VIA_INGRESO as via_ingreso,
    s.MODALIDAD as modalidad,
    s.GRUPO_SERVICIO as grupo_servicio,
    s.COD_SERVICIO as cod_servicio,
    s.COD_PRESTADOR as cod_prestador,
    s.TIPO_DOC_PROFESIONAL as tipo_doc_profesional,
    s.NUM_DOC_PROFESIONAL as num_doc_profesional,
    s.VR_SERVICIO as vr_servicio,
    s.VALOR_PAGO_MODERADOR as valor_pago_moderador,
    s.CONCEPTO_RECAUDO as concepto_recaudo,
    s.NUM_AUTORIZACION as num_autorizacion
FROM SERVICIOS s
WHERE s.NUM_FACTURA = :factura
  AND s.FECHA_ATENCION BETWEEN :fecha_ini AND :fecha_fin""",
        "description": "Consulta procedimientos por factura y rango de fechas"
    },
    {
        "name": "Procedimientos por fecha",
        "query_type": "transaccion",
        "query_text": """SELECT
    s.FACTURA as num_factura,
    s.CODIGO_CUP as cod_procedimiento,
    s.FECHA_ATENCION as fecha_atencion,
    s.COD_DIAGNOSTICO as cod_diagnostico,
    s.FINALIDAD as finalidad,
    s.VIA_INGRESO as via_ingreso,
    s.MODALIDAD as modalidad,
    s.GRUPO_SERVICIO as grupo_servicio,
    s.COD_SERVICIO as cod_servicio,
    s.COD_PRESTADOR as cod_prestador,
    s.TIPO_DOC_PROFESIONAL as tipo_doc_profesional,
    s.NUM_DOC_PROFESIONAL as num_doc_profesional,
    s.VR_SERVICIO as vr_servicio,
    p.TIPO_DOCUMENTO as tipo_doc_paciente,
    p.NUMERO_DOCUMENTO as num_doc_paciente
FROM SERVICIOS s
JOIN USUAHOS p ON s.COD_PACIENTE = p.COD_PACIENTE
WHERE s.FECHA_ATENCION BETWEEN :fecha_ini AND :fecha_fin""",
        "description": "Consulta todos los procedimientos en rango de fechas"
    },
]


def ensure_defaults():
    conn = get_connection()
    for q in QUERY_DEFAULTS:
        exists = conn.execute(
            "SELECT id FROM queries WHERE name = ?", (q["name"],)
        ).fetchone()
        if not exists:
            conn.execute(
                "INSERT INTO queries (name, query_type, query_text, description) VALUES (?, ?, ?, ?)",
                (q["name"], q["query_type"], q["query_text"], q["description"]),
            )
    conn.commit()
    conn.close()


@router.get("")
async def queries_page(request: Request, user: dict = Depends(get_current_user)):
    ensure_defaults()
    conn = get_connection()
    queries = conn.execute("SELECT * FROM queries ORDER BY query_type, name").fetchall()
    conn.close()
    return request.app.state.templates.TemplateResponse("queries.html", {
        "request": request, "user": user, "queries": queries
    })


@router.post("/create")
async def query_create(
    request: Request,
    user: dict = Depends(get_current_user),
    name: str = Form(...),
    query_type: str = Form(...),
    query_text: str = Form(...),
    description: str = Form(""),
):
    conn = get_connection()
    conn.execute(
        "INSERT INTO queries (name, query_type, query_text, description) VALUES (?, ?, ?, ?)",
        (name, query_type, query_text, description),
    )
    conn.commit()
    conn.close()
    return RedirectResponse("/queries", status_code=302)


@router.post("/update/{query_id}")
async def query_update(
    query_id: int,
    request: Request,
    user: dict = Depends(get_current_user),
    name: str = Form(...),
    query_text: str = Form(...),
    description: str = Form(""),
):
    conn = get_connection()
    conn.execute(
        "UPDATE queries SET name = ?, query_text = ?, description = ? WHERE id = ?",
        (name, query_text, description, query_id),
    )
    conn.commit()
    conn.close()
    return RedirectResponse("/queries", status_code=302)


@router.post("/delete/{query_id}")
async def query_delete(query_id: int, user: dict = Depends(get_current_user)):
    conn = get_connection()
    conn.execute("DELETE FROM queries WHERE id = ?", (query_id,))
    conn.commit()
    conn.close()
    return RedirectResponse("/queries", status_code=302)


@router.post("/esquema")
async def obtener_esquema(user: dict = Depends(get_current_user)):
    from app.services.firebird_service import FirebirdService
    conn = get_connection()
    configs = {row["key"]: row["value"] for row in conn.execute("SELECT * FROM config").fetchall()}
    conn.close()

    fb = FirebirdService()
    fb_success, fb_msg = fb.connect(
        configs.get("firebird_host", "localhost"),
        int(configs.get("firebird_port", 3050)),
        configs.get("firebird_database", ""),
        configs.get("firebird_user", "SYSDBA"),
        configs.get("firebird_password", "masterkey"),
    )
    if not fb_success:
        return JSONResponse({"error": f"Error Firebird: {fb_msg}"}, status_code=400)

    success, fb_err, tablas = fb.execute_query("""
        SELECT RDB$RELATION_NAME as nombre
        FROM RDB$RELATIONS
        WHERE RDB$SYSTEM_FLAG = 0
          AND RDB$RELATION_NAME NOT LIKE 'RDB$%'
        ORDER BY 1
    """, {})

    if not success:
        fb.disconnect()
        return JSONResponse({"error": fb_err}, status_code=400)

    resultado = []
    for t in tablas:
        nombre = t["NOMBRE"].strip()
        ok, err, cols = fb.execute_query("""
            SELECT
                rf.RDB$FIELD_NAME as COLUMN_NAME,
                f.RDB$FIELD_TYPE as FIELD_TYPE,
                f.RDB$FIELD_LENGTH as FIELD_LENGTH
            FROM RDB$RELATION_FIELDS rf
            JOIN RDB$FIELDS f ON rf.RDB$FIELD_SOURCE = f.RDB$FIELD_NAME
            WHERE rf.RDB$RELATION_NAME = :tabla
            ORDER BY rf.RDB$FIELD_POSITION
        """, {"tabla": nombre})
        columnas = []
        if ok:
            for c in cols:
                tiponum = c["FIELD_TYPE"]
                tipos = {7: "SMALLINT", 8: "INTEGER", 10: "FLOAT", 12: "DATE", 13: "TIME",
                         14: "CHAR", 16: "BIGINT", 27: "DOUBLE", 35: "TIMESTAMP", 37: "VARCHAR",
                         40: "BLOB", 45: "BLOB_ID", 261: "BLOB"}
                columnas.append({
                    "nombre": c["COLUMN_NAME"].strip(),
                    "tipo": tipos.get(tiponum, f"UNKNOWN({tiponum})"),
                    "longitud": c["FIELD_LENGTH"]
                })
        resultado.append({"tabla": nombre, "columnas": columnas})

    fb.disconnect()
    return JSONResponse({"tablas": resultado})


@router.post("/tablas")
async def listar_tablas(user: dict = Depends(get_current_user)):
    from app.services.firebird_service import FirebirdService
    conn = get_connection()
    configs = {row["key"]: row["value"] for row in conn.execute("SELECT * FROM config").fetchall()}
    conn.close()

    fb = FirebirdService()
    fb_success, fb_msg = fb.connect(
        configs.get("firebird_host", "localhost"),
        int(configs.get("firebird_port", 3050)),
        configs.get("firebird_database", ""),
        configs.get("firebird_user", "SYSDBA"),
        configs.get("firebird_password", "masterkey"),
    )
    if not fb_success:
        return JSONResponse({"error": f"Error Firebird: {fb_msg}"}, status_code=400)

    success, fb_err, rows = fb.execute_query("""
        SELECT RDB$RELATION_NAME as nombre
        FROM RDB$RELATIONS
        WHERE RDB$SYSTEM_FLAG = 0
          AND RDB$RELATION_NAME NOT LIKE 'RDB$%'
        ORDER BY 1
    """, {})
    fb.disconnect()

    if not success:
        return JSONResponse({"error": fb_err}, status_code=400)

    return JSONResponse({
        "tablas": [r["NOMBRE"].strip() for r in rows]
    })


@router.post("/test")
async def query_test(
    request: Request,
    query_id: int = Form(...),
    user: dict = Depends(get_current_user),
):
    from app.services.firebird_service import FirebirdService

    conn = get_connection()
    q = conn.execute("SELECT * FROM queries WHERE id = ?", (query_id,)).fetchone()
    configs = {row["key"]: row["value"] for row in conn.execute("SELECT * FROM config").fetchall()}
    conn.close()

    if not q:
        return JSONResponse({"error": "Consulta no encontrada"}, status_code=404)

    fb = FirebirdService()
    fb_success, fb_msg = fb.connect(
        configs.get("firebird_host", "localhost"),
        int(configs.get("firebird_port", 3050)),
        configs.get("firebird_database", ""),
        configs.get("firebird_user", "SYSDBA"),
        configs.get("firebird_password", "masterkey"),
    )
    if not fb_success:
        return JSONResponse({"error": f"Error Firebird: {fb_msg}"}, status_code=400)

    success, fb_err, rows = fb.execute_query(q["query_text"], {})
    fb.disconnect()

    if not success:
        return JSONResponse({"error": fb_err}, status_code=400)

    limit = rows[:20] if rows else []
    return JSONResponse({
        "rows": limit,
        "total": len(rows),
        "columns": list(limit[0].keys()) if limit else []
    })
