# RIPS Manager — Documentación Completa

**Desarrollado por [U-SITE SAS BIC](https://u-site.app/)**

**Repositorio**: `https://github.com/U-SITE-SAS-BIC/rips_manager`

Sistema web para generar y enviar JSON de RIPS (Registro Individual de Prestación de Servicios de Salud) según la **Resolución 2275 de 2023** del Ministerio de Salud y Protección Social de Colombia.

---

## 1. Arquitectura

```
                     ┌────────────────────┐
                     │    Navegador       │
                     │  Tailwind + CM     │
                     └────────┬───────────┘
                              │ HTTP
                     ┌────────▼───────────┐
                     │  FastAPI (8080)    │
                     │  + Jinja2          │
                     │  + Auth Middleware │
                     └───┬────┬────┬──────┘
                         │    │    │
              ┌──────────┘    │    └──────────┐
              ▼               ▼               ▼
        ┌──────────┐   ┌──────────┐   ┌──────────────┐
        │ Firebird │   │  SQLite  │   │  API externa │
        │ (datos)  │   │ (app.db) │   │  (receptor)  │
        └──────────┘   └──────────┘   └──────────────┘
```

### Stack Tecnológico

| Componente | Tecnología | Versión |
|---|---|---|
| Backend | FastAPI | 0.115.6 |
| Servidor ASGI | Uvicorn | 0.34.0 |
| Templates | Jinja2 | 3.1.5 |
| CSS | Tailwind CSS | CDN |
| Editor SQL | CodeMirror | 5.65.16 CDN |
| BD de la app | SQLite | — |
| BD de datos | Firebird | vía fdb >= 2.0.0 |
| Autenticación | python-jose (JWT) + bcrypt | 3.3.0 / 4.2.1 |
| Cliente HTTP | httpx | 0.28.1 |
| Multipart | python-multipart | 0.0.20 |
| Archivos async | aiofiles | 24.1.0 |

---

## 2. Endpoints (20 totales)

### Autenticación — `app/routes/auth.py`

| Método | Ruta | Descripción | Auth |
|---|---|---|---|
| GET | `/auth/login` | Página de inicio de sesión | Pública |
| POST | `/auth/login` | Procesa login, setea cookie HttpOnly con JWT | Pública |
| GET | `/auth/register` | Página de registro | Pública |
| POST | `/auth/register` | Crea usuario (username, email, password) | Pública |
| GET | `/auth/logout` | Elimina cookie, redirige a login | Pública |
| POST | `/auth/api/login` | Login API, devuelve `{"access_token": "...", "token_type": "bearer"}` | Pública |

### Dashboard — `app/routes/dashboard.py`

| Método | Ruta | Descripción | Auth |
|---|---|---|---|
| GET | `/dashboard` | Estadísticas: total envíos exitosos/errores, últimos 10 registros | Requerida |

### Configuración — `app/routes/config.py`

| Método | Ruta | Descripción | Auth |
|---|---|---|---|
| GET | `/config` | Página de configuración (Firebird, API, prestador) | Requerida |
| POST | `/config/save` | Guarda configuración (11 claves) | Requerida |

### Consultas SQL — `app/routes/queries.py`

| Método | Ruta | Descripción | Auth |
|---|---|---|---|
| GET | `/queries` | Página con 3 pestañas: Probador / Constructor / Editor | Requerida |
| POST | `/queries/run-sql` | Ejecuta SQL raw contra Firebird (max 200 filas) | Requerida |
| POST | `/queries/test` | Prueba consulta guardada (max 20 filas) | Requerida |
| POST | `/queries/esquema` | Devuelve esquema completo: tablas + columnas + tipos | Requerida |
| POST | `/queries/tablas` | Lista nombres de tablas | Requerida |
| POST | `/queries/create` | Crea nueva consulta | Requerida |
| POST | `/queries/update/{id}` | Actualiza consulta | Requerida |
| POST | `/queries/delete/{id}` | Elimina consulta | Requerida |

### Terceros — `app/routes/terceros.py`

| Método | Ruta | Descripción | Auth |
|---|---|---|---|
| GET | `/terceros` | Página de envío de terceros | Requerida |
| POST | `/terceros/test-connection` | Prueba conexión Firebird | Requerida |
| POST | `/terceros/preview` | Vista previa del JSON de terceros | Requerida |
| POST | `/terceros/send` | Genera y envía JSON de terceros a la API | Requerida |

### Transacción RIPS — `app/routes/transaccion.py`

| Método | Ruta | Descripción | Auth |
|---|---|---|---|
| GET | `/transaccion` | Página de envío de transacción RIPS | Requerida |
| POST | `/transaccion/preview` | Vista previa del JSON de transacción | Requerida |
| POST | `/transaccion/send` | Genera y envía JSON de transacción a la API | Requerida |

### Automatización — `app/routes/automation.py`

| Método | Ruta | Descripción | Auth |
|---|---|---|---|
| GET | `/automation` | Página de automatización (2 pasos) | Requerida |
| POST | `/automation/run` | Paso 1 (terceros) + Paso 2 (transacción) por rango de fechas | Requerida |

### Logs — `app/routes/logs.py`

| Método | Ruta | Descripción | Auth |
|---|---|---|---|
| GET | `/logs` | Historial de envíos con filtros (tipo, status, factura) | Requerida |

### Root

| Método | Ruta | Descripción | Auth |
|---|---|---|---|
| GET | `/` | Redirige a `/dashboard` | Pública |

---

## 3. Modelo de Base de Datos

### SQLite (`rips_manager.db`)

#### Tabla `users`
| Columna | Tipo | Descripción |
|---|---|---|
| id | INTEGER PK AUTOINCREMENT | ID único |
| username | TEXT UNIQUE NOT NULL | Nombre de usuario |
| email | TEXT UNIQUE NOT NULL | Correo electrónico |
| password_hash | TEXT NOT NULL | Hash bcrypt |
| created_at | TEXT DEFAULT datetime('now') | Fecha de creación |

#### Tabla `config`
| Columna | Tipo | Descripción |
|---|---|---|
| id | INTEGER PK AUTOINCREMENT | ID único |
| key | TEXT UNIQUE NOT NULL | Clave de configuración |
| value | TEXT | Valor |

**Claves predefinidas:**

| Clave | Default | Descripción |
|---|---|---|
| `firebird_host` | `localhost` | Host Firebird |
| `firebird_port` | `3050` | Puerto Firebird |
| `firebird_database` | — | Ruta BD Firebird |
| `firebird_user` | `SYSDBA` | Usuario Firebird |
| `firebird_password` | `masterkey` | Contraseña Firebird |
| `api_url` | — | URL de la API destino |
| `api_method` | `POST` | Método HTTP (POST/PUT) |
| `api_key` | — | API Key (Bearer token) |
| `api_timeout` | `30` | Timeout en segundos |
| `num_documento_obligado` | — | NIT del prestador |
| `cod_prestador` | — | Código del prestador |

#### Tabla `queries`
| Columna | Tipo | Descripción |
|---|---|---|
| id | INTEGER PK AUTOINCREMENT | ID único |
| name | TEXT NOT NULL | Nombre descriptivo |
| query_type | TEXT NOT NULL | `terceros` o `transaccion` |
| query_text | TEXT NOT NULL | SQL con parámetros `:param` |
| description | TEXT | Descripción |
| created_at | TEXT DEFAULT datetime('now') | Fecha de creación |

**Consultas por defecto** (3):
1. `Terceros - Datos del paciente` — Busca paciente por `:doc_num`
2. `Procedimientos por factura` — Busca servicios por `:factura`, `:fecha_ini`, `:fecha_fin`
3. `Procedimientos por fecha` — JOIN servicios + pacientes por rango de fechas

#### Tabla `envios`
| Columna | Tipo | Descripción |
|---|---|---|
| id | INTEGER PK AUTOINCREMENT | ID único |
| user_id | INTEGER FK → users(id) | Usuario que envió |
| tipo | TEXT NOT NULL | `terceros` o `transaccion` |
| factura | TEXT | Número de factura |
| fecha_inicio | TEXT | Inicio del rango |
| fecha_fin | TEXT | Fin del rango |
| pacientes_count | INTEGER DEFAULT 0 | Cantidad de pacientes |
| servicios_count | INTEGER DEFAULT 0 | Cantidad de servicios |
| status | TEXT NOT NULL DEFAULT 'pendiente' | `success` o `error` |
| json_enviado | TEXT | JSON completo enviado |
| respuesta_api | TEXT | Respuesta de la API |
| codigo_cuv | TEXT | Código CUV (si aplica) |
| created_at | TEXT DEFAULT datetime('now') | Fecha del envío |

---

## 4. Autenticación

### Flujo Login
```
Navegador                    Servidor
   │                           │
   │── POST /auth/login ──────▶│ (username + password)
   │                           │── verifica bcrypt
   │                           │── genera JWT HS256
   │◀── 302 /dashboard ────────│ (Set-Cookie: token=JWT; HttpOnly)
   │                           │
   │── GET /dashboard ────────▶│ (Cookie: token=JWT)
   │                           │── middleware decodifica JWT
   │                           │── request.state.user = payload
   │◀──── HTML dashboard ──────│
```

### Middleware (`main.py:48-68`)
- Rutas públicas: `/auth/login`, `/auth/register`, `/auth/api/login`, `/static/*`
- Lee token de: `Cookie: token` → `Authorization: Bearer`
- Si inválido y `/api/` → 401 JSON; si HTML → redirect `/auth/login`

### JWT
- Algoritmo: HS256
- Clave: `rips-manager-secret-key-change-in-production`
- Payload: `{user_id, username}` (sin expiración)

---

## 5. Estructuras JSON

### JSON Terceros (17 campos)
```json
{
  "tipoDocumentoIdentificacion": "CC",
  "numDocumentoIdentificacion": "27765610",
  "primerNombre": "MARIA",
  "segundoNombre": "ELENA",
  "primerApellido": "GOMEZ",
  "segundoApellido": "RUIZ",
  "fechaNacimiento": "1954-01-19",
  "codSexo": "F",
  "codEntidadAdministradora": "EPS010",
  "tipoUsuario": "01",
  "codPaisResidencia": "170",
  "codMunicipioResidencia": "54001",
  "codZonaTerritorialResidencia": "01",
  "incapacidad": "NO",
  "codPaisOrigen": "170",
  "direccionResidencia": "CRA 5 #10-20",
  "codZonaResidencia": "01"
}
```

### JSON Procedimiento (20 campos P01-P20)
```json
{
  "consecutivo": 1,
  "codProcedimiento": "903841",
  "fechaInicioAtencion": "2026-06-11 00:00",
  "codDiagnosticoPrincipal": "R790",
  "codDiagnosticoRelacionado": null,
  "finalidadTecnologiaSalud": "23",
  "viaIngresoServicioSalud": "02",
  "modalidadGrupoServicioTecSal": "01",
  "grupoServicios": "02",
  "codServicio": 706,
  "codPrestador": "540010152002",
  "tipoDocumentoIdentificacion": "CC",
  "numDocumentoIdentificacion": "27898369",
  "vrServicio": 8000,
  "valorPagoModerador": 0,
  "conceptoRecaudo": "05",
  "numAutorizacion": null,
  "idMIPRES": null,
  "codComplicacion": null,
  "numFEVPagoModerador": null
}
```

### JSON Transacción
```json
{
  "numDocumentoIdObligado": "900278729",
  "numFactura": "LHXC03404",
  "tipoNota": null,
  "numNota": null,
  "usuarios": [{
    "tipoDocumentoIdentificacion": "CC",
    "numDocumentoIdentificacion": "27765610",
    "codEntidadAdministradora": "EPS010",
    "tipoUsuario": "12",
    "fechaNacimiento": "1954-01-19",
    "codSexo": "F",
    "codPaisResidencia": "170",
    "codMunicipioResidencia": "54001",
    "codZonaTerritorialResidencia": "02",
    "incapacidad": "NO",
    "consecutivo": 1,
    "codPaisOrigen": "170",
    "servicios": {
      "procedimientos": [
        { /* procedimiento */ }
      ]
    }
  }]
}
```

---

## 6. Flujo de Datos

### Terceros
```
1. Config → leer firebird_host, api_url, etc.
2. Firebird → conectar + ejecutar query → filas
3. Mapear fila → JSON (generar_terceros)
4. httpx → POST/PUT {api_url}/terceros
5. Guardar en envios (JSON + respuesta)
```

### Transacción
```
1. Config → leer Firebird + API
2. Firebird → ejecutar query → filas
3. Agrupar por (factura, paciente)
4. Cada grupo → JSON (generar_transaccion)
5. Cada grupo → httpx → {api_url}/transaccion
6. Cada envío → log en envios
```

### Automatización
```
Paso 1: Terceros
  - Query tipo 'terceros' por rango de fechas
  - Deduplicar por documento
  - Enviar cada uno

Paso 2: Transacción
  - Query tipo 'transaccion' por mismo rango
  - Agrupar por factura
  - Enviar cada grupo agrupado
```

---

## 7. Parámetros en Consultas SQL

| Parámetro | Ejemplo | Descripción |
|---|---|---|
| `:doc_num` | `WHERE doc = :doc_num` | Filtrar por documento |
| `:factura` | `WHERE factura = :factura` | Filtrar por factura |
| `:fecha_ini` | `WHERE fecha >= :fecha_ini` | Fecha inicio |
| `:fecha_fin` | `WHERE fecha <= :fecha_fin` | Fecha fin |

---

## 8. Estructura del Proyecto

```
rips_manager/
├── main.py                         # Entry point, middleware, rutas
├── requirements.txt                # 9 dependencias
├── rips_manager.db                 # SQLite (autogenerado)
├── README.md                       # Documentación de usuario
├── DOCUMENTACION.md                # Documentación técnica
├── ejemplo_terceros.json           # JSON ejemplo
├── ejemplo_transaccion_rips.json   # JSON ejemplo
├── arrancar.sh                     # Inicio macOS/Linux
├── run.bat                         # Inicio Windows (minimizado)
├── run.ps1                         # Inicio Windows PowerShell
├── run.vbs                         # Inicio Windows (sin ventana)
├── stop.bat                        # Detener servidor
├── app/
│   ├── __init__.py
│   ├── auth.py                     # JWT, bcrypt, get_current_user
│   ├── database.py                 # SQLite init y conexión
│   ├── models.py                   # Pydantic models
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py                 # Login, register, logout
│   │   ├── dashboard.py            # Estadísticas
│   │   ├── config.py               # Configuración
│   │   ├── queries.py              # CRUD + Probador + Constructor
│   │   ├── terceros.py             # Envío terceros
│   │   ├── transaccion.py          # Envío transacción
│   │   ├── automation.py           # Automatización 2 pasos
│   │   └── logs.py                 # Historial
│   ├── services/
│   │   ├── __init__.py
│   │   ├── firebird_service.py     # Conexión y consultas Firebird
│   │   ├── json_generator.py       # Construcción de JSON RIPS
│   │   └── api_client.py           # Envío HTTP
│   └── templates/
│       ├── base.html               # Layout (sidebar, Tailwind, CodeMirror, FontAwesome)
│       ├── login.html
│       ├── register.html
│       ├── dashboard.html
│       ├── config.html
│       ├── queries.html            # Probador / Constructor / Editor
│       ├── terceros.html
│       ├── transaccion.html
│       ├── automation.html
│       └── logs.html
```

---

## 9. Cómo Ejecutar

### Windows
```powershell
git clone https://github.com/U-SITE-SAS-BIC/rips_manager.git
cd rips_manager
powershell -ExecutionPolicy Bypass -File run.ps1
```
O doble clic en `run.bat` (inicia minimizado).

### macOS / Linux
```bash
git clone https://github.com/U-SITE-SAS-BIC/rips_manager.git
cd rips_manager
chmod +x arrancar.sh
./arrancar.sh
```

### Acceder
- Local: `http://localhost:8080`
- Red: `http://<IP_LOCAL>:8080`

---

## 10. Primer Uso

1. Abrir `http://localhost:8080/auth/register`
2. Crear usuario y contraseña
3. Iniciar sesión
4. Ir a **Configuración** → configurar Firebird, API, datos del prestador
5. Ir a **Consultas SQL** → ajustar/queries a nombres reales de tablas
6. Usar el **Probador** para probar consultas
7. Usar **Terceros**, **Transacción RIPS** o **Automatización**

---

## 11. Créditos

© 2026 **U-SITE SAS BIC** — Todos los derechos reservados.

- **Web**: [https://u-site.app/](https://u-site.app/)
- **Sistema**: RIPS Manager v1.0
- **Propósito**: Generación y envío de RIPS según Res. 2275/2023
- **Campos cubiertos**: Procedimientos (20 campos P01-P20 del Anexo Técnico 1)
