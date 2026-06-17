from fastapi import APIRouter, Request, Depends
from app.database import get_connection
from app.auth import get_current_user

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("")
async def logs_page(
    request: Request,
    user: dict = Depends(get_current_user),
    tipo: str = "",
    status: str = "",
    factura: str = "",
):
    conn = get_connection()

    where = ["1=1"]
    params = []

    if tipo:
        where.append("e.tipo = ?")
        params.append(tipo)
    if status:
        where.append("e.status = ?")
        params.append(status)
    if factura:
        where.append("e.factura LIKE ?")
        params.append(f"%{factura}%")

    envios = conn.execute(f"""
        SELECT e.*, u.username FROM envios e
        LEFT JOIN users u ON e.user_id = u.id
        WHERE {' AND '.join(where)}
        ORDER BY e.created_at DESC LIMIT 100
    """, params).fetchall()

    stats = conn.execute("""
        SELECT
            tipo,
            status,
            COUNT(*) as total,
            SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as exitosos,
            SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as fallidos
        FROM envios
        GROUP BY tipo, status
    """).fetchall()

    conn.close()

    return request.app.state.templates.TemplateResponse("logs.html", {
        "request": request, "user": user,
        "envios": envios, "stats": stats,
        "filtro_tipo": tipo, "filtro_status": status, "filtro_factura": factura,
    })
