# RIPS Manager — Documentación Técnica

Sistema web para generar y enviar JSON de RIPS (Res. 2275/2023) a una API, conectándose a una base de datos Firebird.

---

## Arquitectura

```
┌─────────────┐     ┌──────────────────┐     ┌──────────────┐
│  Navegador  │────▶│  FastAPI (8080)  │────▶│  Firebird BD │
│  (Tailwind) │◀────│  + Jinja2        │◀────│  (datos)     │
└─────────────┘     └──────────────────┘     └──────────────┘
                          │
                          ▼
                    ┌──────────────┐
                    │  SQLite      │
                    │  (app.db)    │
                    └──────────────┘
                          │
                          ▼
                    ┌──────────────┐
                    │  API externa │
                    │  (envío RIPS)│
                    └──────────────┘
```

## Stack técnico

| Componente | Tecnología |
|---|---|
| Backend | Python 3.9+ / FastAPI |
| Frontend | Jinja2 + Tailwind CSS (CDN) + FontAwesome |
| Base de datos app | SQLite (usuarios, config, logs, queries) |
| Base de datos datos | Firebird (vía `fdb`) |
| Autenticación | JWT + bcrypt + HttpOnly cookies |
| Cliente HTTP | httpx (async) |
| Servidor | uvicorn |

---

## Endpoints (20 totales)

### Autenticación (6 endpoints)

| Método | Ruta | Descripción | Autenticación |
|---|---|---|---|
| GET | `/auth/login` | Página de inicio de sesión | Pública |
| POST | `/auth/login` | Procesa login, devuelve cookie JWT | Pública |
| GET | `/auth/register` | Página de registro | Pública |
| POST | `/auth/register` | Registra nuevo usuario | Pública |
| GET | `/auth/logout` | Cierra sesión (elimina cookie) | Pública |
| POST | `/auth/api/login` | Login vía API (devuelve token JSON) | Pública |

### Dashboard (1 endpoint)

| Método | Ruta | Descripción | Autenticación |
|---|---|---|---|
| GET | `/dashboard` | Estadísticas de envíos, últimos registros | Requerida |

### Configuración (2 endpoints)

| Método | Ruta | Descripción | Autenticación |
|---|---|---|---|
| GET | `/config` | Página de configuración (Firebird + API + prestador) | Requerida |
| POST | `/config/save` | Guarda toda la configuración | Requerida |

### Consultas SQL (3 endpoints)

| Método | Ruta | Descripción | Autenticación |
|---|---|---|---|
| GET | `/queries` | Página de gestión de consultas SQL | Requerida |
| POST | `/queries/create` | Crea nueva consulta SQL | Requerida |
| POST | `/queries/delete/{id}` | Elimina consulta SQL | Requerida |
| POST | `/queries/update/{id}` | Actualiza consulta SQL | Requerida |

### Terceros (3 endpoints)

| Método | Ruta | Descripción | Autenticación |
|---|---|---|---|
| GET | `/terceros` | Página de envío de terceros | Requerida |
| POST | `/terceros/test-connection` | Prueba conexión Firebird | Requerida |
| POST | `/terceros/preview` | Vista previa del JSON de terceros | Requerida |
| POST | `/terceros/send` | Genera y envía JSON de terceros a la API | Requerida |

### Transacción RIPS (3 endpoints)

| Método | Ruta | Descripción | Autenticación |
|---|---|---|---|
| GET | `/transaccion` | Página de envío de transacción RIPS | Requerida |
| POST | `/transaccion/preview` | Vista previa del JSON de transacción | Requerida |
| POST | `/transaccion/send` | Genera y envía JSON de transacción a la API | Requerida |

### Automatización (2 endpoints)

| Método | Ruta | Descripción | Autenticación |
|---|---|---|---|
| GET | `/automation` | Página de automatización 2 pasos | Requerida |
| POST | `/automation/run` | Ejecuta Paso 1 (terceros) + Paso 2 (transacción) | Requerida |

### Logs (1 endpoint)

| Método | Ruta | Descripción | Autenticación |
|---|---|---|---|
| GET | `/logs` | Historial de envíos con filtros | Requerida |

---

## Flujo de autenticación

```
Navegador                    Servidor
   │                           │
   │── GET /auth/login ───────▶│
   │◀──── HTML login page ─────│
   │                           │
   │── POST /auth/login ───────▶│ (username + password)
   │                           │── verifica credenciales
   │                           │── genera JWT
   │◀── 302 /dashboard ────────│ (Set-Cookie: token=JWT; HttpOnly)
   │                           │
   │── GET /dashboard ────────▶│ (Cookie: token=JWT)
   │                           │── middleware verifica JWT
   │                           │── setea request.state.user
   │◀──── HTML dashboard ──────│
```

- **Cookie HttpOnly**: no accesible desde JavaScript (seguridad XSS)
- **JWT expira en 12 horas**
- **Bearer token** también soportado para llamadas API (`Authorization: Bearer <token>`)

---

## Flujo de envío de RIPS

### Manual (página Terceros + Transacción)

```
1. Configurar conexión Firebird y API (una vez)
2. Definir consultas SQL en "Consultas SQL"
3. Ir a "Terceros" → seleccionar consulta → "Vista Previa" → "Enviar a API"
4. Ir a "Transacción RIPS" → seleccionar consulta + fechas → "Enviar a API"
```

### Automatizado (página Automatización)

```
1. Seleccionar consulta de terceros (Paso 1)
2. Seleccionar consulta de transacción (Paso 2)
3. Definir rango de fechas
4. "Ejecutar Automatización Completa"
   └── Paso 1: Envía todos los terceros del período
   └── Paso 2: Envía todas las transacciones del período
```

### Estructura de los JSON generados

#### JSON Terceros
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
  "tipoUsuario": "12",
  "codPaisResidencia": "170",
  "codMunicipioResidencia": "54001",
  "codZonaTerritorialResidencia": "02",
  "incapacidad": "NO",
  "codPaisOrigen": "170",
  "direccionResidencia": "CRA 5 #10-20",
  "codZonaResidencia": "02"
}
```

#### JSON Transacción RIPS
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
      "procedimientos": [{
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
      }]
    }
  }]
}
```

---

## Base de datos SQLite (app)

### Tabla `users`
| Columna | Tipo | Descripción |
|---|---|---|
| id | INTEGER PK | Auto-incrementable |
| username | TEXT UNIQUE | Nombre de usuario |
| email | TEXT UNIQUE | Correo electrónico |
| password_hash | TEXT | Hash bcrypt de la contraseña |
| created_at | TEXT | Fecha de creación |

### Tabla `config`
| Columna | Tipo | Descripción |
|---|---|---|
| id | INTEGER PK | Auto-incrementable |
| key | TEXT UNIQUE | Clave de configuración |
| value | TEXT | Valor |

Claves predefinidas:
- `firebird_host`, `firebird_port`, `firebird_database`, `firebird_user`, `firebird_password`
- `api_url`, `api_method`, `api_key`, `api_timeout`
- `num_documento_obligado`, `cod_prestador`

### Tabla `queries`
| Columna | Tipo | Descripción |
|---|---|---|
| id | INTEGER PK | Auto-incrementable |
| name | TEXT | Nombre descriptivo |
| query_type | TEXT | `terceros` o `transaccion` |
| query_text | TEXT | Sentencia SQL con parámetros |
| description | TEXT | Descripción |
| created_at | TEXT | Fecha de creación |

### Tabla `envios`
| Columna | Tipo | Descripción |
|---|---|---|
| id | INTEGER PK | Auto-incrementable |
| user_id | INTEGER FK | Usuario que realizó el envío |
| tipo | TEXT | `terceros` o `transaccion` |
| factura | TEXT | Número de factura |
| fecha_inicio / fecha_fin | TEXT | Rango de fechas del envío |
| pacientes_count / servicios_count | INTEGER | Cantidades |
| status | TEXT | `success` o `error` |
| json_enviado | TEXT | JSON completo enviado |
| respuesta_api | TEXT | Respuesta de la API |
| codigo_cuv | TEXT | Código CUV (si aplica) |
| created_at | TEXT | Fecha del envío |

---

## Parámetros en consultas SQL

Las consultas pueden usar estos parámetros que el sistema reemplaza automáticamente:

| Parámetro | Ejemplo | Uso |
|---|---|---|
| `:doc_num` | `WHERE doc = :doc_num` | Filtrar por documento de paciente |
| `:factura` | `WHERE fact = :factura` | Filtrar por número de factura |
| `:fecha_ini` | `WHERE fecha >= :fecha_ini` | Fecha inicio del rango |
| `:fecha_fin` | `WHERE fecha <= :fecha_fin` | Fecha fin del rango |

---

## Estructura del proyecto

```
rips_manager/
├── main.py                  # Entry point, middleware, rutas
├── requirements.txt         # Dependencias Python
├── rips_manager.db          # SQLite (autogenerado)
├── DOCUMENTACION.md         # Este archivo
├── README.md                # Documentación de RIPS
├── ejemplo_terceros.json    # JSON de ejemplo terceros
├── ejemplo_transaccion_rips.json  # JSON de ejemplo transacción
├── app/
│   ├── __init__.py
│   ├── auth.py              # JWT, bcrypt, get_current_user
│   ├── database.py          # SQLite init y conexión
│   ├── models.py            # Pydantic models
│   ├── routes/
│   │   ├── auth.py          # Login, register, logout
│   │   ├── dashboard.py     # Página principal con stats
│   │   ├── config.py        # Configuración Firebird + API
│   │   ├── queries.py       # CRUD de consultas SQL
│   │   ├── terceros.py      # Generar y enviar JSON terceros
│   │   ├── transaccion.py   # Generar y enviar JSON transacción
│   │   ├── automation.py    # Paso 1 + Paso 2 automático
│   │   └── logs.py          # Historial de envíos
│   ├── services/
│   │   ├── firebird_service.py  # Conexión y consultas Firebird
│   │   ├── json_generator.py    # Construcción de JSON RIPS
│   │   └── api_client.py        # Envío HTTP a API externa
│   └── templates/           # 10 plantillas Jinja2 + Tailwind
```

---

## Cómo ejecutar

```bash
cd /Users/lizandro/Documents/proyectos/rips_manager
pip3 install -r requirements.txt
python3 main.py
```

Abrir en el navegador: **http://localhost:8080**

---

## Secuencia para primer uso

1. Abrir http://localhost:8080/auth/register
2. Crear usuario y contraseña
3. Iniciar sesión
4. Ir a **Configuración** → configurar Firebird, API, datos del prestador
5. Ir a **Consultas SQL** → ajustar las queries a los nombres reales de tablas
6. Usar **Terceros**, **Transacción RIPS** o **Automatización**
