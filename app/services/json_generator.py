from collections import defaultdict
from datetime import datetime
from typing import Optional


def generar_terceros(row: dict) -> dict:
    return {
        "tipoDocumentoIdentificacion": row.get("tipo_documento", "CC"),
        "numDocumentoIdentificacion": row.get("numero_documento", ""),
        "primerNombre": (row.get("primer_nombre") or "").upper(),
        "segundoNombre": (row.get("segundo_nombre") or "").upper(),
        "primerApellido": (row.get("primer_apellido") or "").upper(),
        "segundoApellido": (row.get("segundo_apellido") or "").upper(),
        "fechaNacimiento": str(row.get("fecha_nacimiento", ""))[:10],
        "codSexo": row.get("cod_sexo", "M"),
        "codEntidadAdministradora": row.get("cod_entidad", ""),
        "tipoUsuario": row.get("tipo_usuario", "01"),
        "codPaisResidencia": row.get("cod_pais", "170"),
        "codMunicipioResidencia": row.get("cod_municipio", ""),
        "codZonaTerritorialResidencia": row.get("cod_zona", "01"),
        "incapacidad": row.get("incapacidad", "NO"),
        "codPaisOrigen": row.get("cod_pais_origen", "170"),
        "direccionResidencia": row.get("direccion", ""),
        "codZonaResidencia": row.get("cod_zona", "01"),
    }


def generar_procedimiento(row: dict, consecutivo: int) -> dict:
    return {
        "consecutivo": consecutivo,
        "codProcedimiento": row.get("cod_procedimiento", ""),
        "fechaInicioAtencion": str(row.get("fecha_atencion", datetime.now().strftime("%Y-%m-%d %H:%M")))[:16],
        "codDiagnosticoPrincipal": row.get("cod_diagnostico", "R790"),
        "codDiagnosticoRelacionado": row.get("cod_diagnostico_rel", None),
        "finalidadTecnologiaSalud": row.get("finalidad", "23"),
        "viaIngresoServicioSalud": row.get("via_ingreso", "02"),
        "modalidadGrupoServicioTecSal": row.get("modalidad", "01"),
        "grupoServicios": row.get("grupo_servicio", "02"),
        "codServicio": int(row.get("cod_servicio", 706)),
        "codPrestador": row.get("cod_prestador", ""),
        "tipoDocumentoIdentificacion": row.get("tipo_doc_profesional", "CC"),
        "numDocumentoIdentificacion": row.get("num_doc_profesional", ""),
        "vrServicio": int(row.get("vr_servicio", 0)),
        "valorPagoModerador": int(row.get("valor_pago_moderador", 0)),
        "conceptoRecaudo": row.get("concepto_recaudo", "05"),
        "numAutorizacion": row.get("num_autorizacion", None),
        "idMIPRES": row.get("id_mipres", None),
        "codComplicacion": row.get("cod_complicacion", None),
        "numFEVPagoModerador": row.get("num_fev_pago_moderador", None),
    }


def agrupar_por_factura(rows: list, factura_default: str = "") -> dict:
    grupos = defaultdict(lambda: {"factura": "", "procedimientos": []})
    for row in rows:
        doc_key = (row.get("tipo_doc_paciente", "CC"), row.get("num_doc_paciente", ""))
        fact = row.get("num_factura", factura_default)
        grupos[(fact, doc_key)]["factura"] = fact
        grupos[(fact, doc_key)]["procedimientos"].append(dict(row))
    return grupos


def generar_transaccion(
    factura: str,
    num_doc_obligado: str,
    rows_tercero: Optional[dict],
    rows_procedimientos: list,
) -> dict:
    transaccion = {
        "numDocumentoIdObligado": num_doc_obligado,
        "numFactura": factura,
        "tipoNota": None,
        "numNota": None,
        "usuarios": [],
    }

    if rows_tercero and rows_procedimientos:
        usuario = {
            "tipoDocumentoIdentificacion": rows_tercero.get("tipoDocumentoIdentificacion", "CC"),
            "numDocumentoIdentificacion": rows_tercero.get("numDocumentoIdentificacion", ""),
            "codEntidadAdministradora": rows_tercero.get("codEntidadAdministradora", ""),
            "tipoUsuario": rows_tercero.get("tipoUsuario", "01"),
            "fechaNacimiento": rows_tercero.get("fechaNacimiento", ""),
            "codSexo": rows_tercero.get("codSexo", "M"),
            "codPaisResidencia": rows_tercero.get("codPaisResidencia", "170"),
            "codMunicipioResidencia": rows_tercero.get("codMunicipioResidencia", ""),
            "codZonaTerritorialResidencia": rows_tercero.get("codZonaTerritorialResidencia", "01"),
            "incapacidad": rows_tercero.get("incapacidad", "NO"),
            "consecutivo": 1,
            "codPaisOrigen": rows_tercero.get("codPaisOrigen", "170"),
            "servicios": {
                "procedimientos": [
                    generar_procedimiento(p, i + 1)
                    for i, p in enumerate(rows_procedimientos)
                ]
            },
        }
        transaccion["usuarios"].append(usuario)

    return transaccion
