from fastapi import APIRouter, Request, Depends
from app.database import get_connection
from app.auth import get_current_user

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard")
async def dashboard(request: Request, user: dict = Depends(get_current_user)):
    conn = get_connection()
    try:
        stats = conn.execute("""
            SELECT
                (SELECT COUNT(*) FROM envios WHERE status = 'success') as total_exitosos,
                (SELECT COUNT(*) FROM envios WHERE status = 'error') as total_errores,
                (SELECT COUNT(*) FROM envios WHERE tipo = 'terceros') as total_terceros,
                (SELECT COUNT(*) FROM envios WHERE tipo = 'transaccion') as total_transacciones,
                (SELECT COUNT(DISTINCT factura) FROM envios WHERE factura IS NOT NULL) as total_facturas
        """).fetchone()

        ultimos = conn.execute("""
            SELECT e.*, u.username FROM envios e
            LEFT JOIN users u ON e.user_id = u.id
            ORDER BY e.created_at DESC LIMIT 10
        """).fetchall()

        return request.app.state.templates.TemplateResponse("dashboard.html", {
            "request": request, "user": user, "stats": stats, "ultimos": ultimos
        })
    finally:
        conn.close()
