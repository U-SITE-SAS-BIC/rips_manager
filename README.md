# RIPS Manager

**Desarrollado por [U-SITE SAS BIC](https://u-site.app/)**

Sistema web para la generación y envío de JSON de RIPS (Registro Individual de Prestación de Servicios de Salud) según la **Resolución 2275 de 2023** del Ministerio de Salud y Protección Social de Colombia.

---

## Requisitos del sistema

- **Python 3.9+** (el script `run.ps1` lo descarga automáticamente si no está instalado)
- **Git** (para actualizaciones via `git pull`)
- **Conexión a base de datos Firebird** (servidor remoto o local)
- **API destino** para recepción de RIPS (configurable)
- **Sistema operativo**: Windows 10/11, macOS, Linux

## Instalación

### Windows

```powershell
git clone https://github.com/U-SITE-SAS-BIC/rips_manager.git
cd rips_manager
powershell -ExecutionPolicy Bypass -File run.ps1
```

El script descarga Python automáticamente si es necesario.

### macOS / Linux

```bash
git clone https://github.com/U-SITE-SAS-BIC/rips_manager.git
cd rips_manager
chmod +x arrancar.sh
./arrancar.sh
```

Una vez iniciado, abrir en el navegador:

- **http://localhost:8080** (en la misma máquina)
- **http://<IP_LOCAL>:8080** (desde otros equipos en la red)

## Primer uso

1. Registrar un usuario en `/auth/register`
2. Iniciar sesión
3. Configurar conexión Firebird y datos del prestador en `/config`
4. Ajustar consultas SQL en `/queries` según los nombres reales de tablas
5. Usar la sección **Terceros**, **Transacción RIPS** o **Automatización**

## Funcionalidades

| Módulo | Descripción |
|---|---|
| **Dashboard** | Estadísticas de envíos, últimos registros |
| **Configuración** | Conexión Firebird, API destino, datos del prestador |
| **Consultas SQL** | Editor de consultas con parámetros (`:doc_num`, `:fecha_ini`, etc.) |
| **Terceros** | Genera y envía JSON de datos maestros del paciente |
| **Transacción RIPS** | Genera y envía JSON de procedimientos (20 campos P01-P20) |
| **Automatización** | Paso 1 (terceros) + Paso 2 (transacción) por rango de fechas |
| **Historial** | Logs de todos los envíos realizados |

## Stack tecnológico

- **Backend**: Python / FastAPI + Uvicorn
- **Frontend**: Jinja2 + Tailwind CSS + FontAwesome
- **Autenticación**: JWT + bcrypt + HttpOnly cookies
- **Base de datos app**: SQLite
- **Base de datos datos**: Firebird (vía `fdb`)
- **Cliente HTTP**: httpx

## Créditos

© 2026 **U-SITE SAS BIC** — Todos los derechos reservados.

- **Web**: [https://u-site.app/](https://u-site.app/)
- **Sistema**: RIPS Manager v1.0
- **Propósito**: Generación y envío de RIPS según Res. 2275/2023
- **Campos cubiertos**: Procedimientos (20 campos P01-P20 del Anexo Técnico 1)

---

*Documentación técnica completa en [DOCUMENTACION.md](DOCUMENTACION.md)*
