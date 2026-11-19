"""
MODELO - Acceso a datos (version de la app web).
Igual al del parcial, pero lee todo de JSON (la app no necesita pandas ni Excel).
- data/red_gamefolks.json: usuarios, relaciones, eventos, ganadores y catalogo.
- data/reportes_moderacion.json: los reportes del Corte 1 (los mismos del Excel).
"""
import json
import os
from .heap import Reporte

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_RED = os.path.join(RAIZ, "data", "red_gamefolks.json")
RUTA_REPORTES = os.path.join(RAIZ, "data", "reportes_moderacion.json")
RUTA_ORDEN = os.path.join(RAIZ, "data", "orden_atencion_moderacion.json")
RUTA_EVIDENCIA = os.path.join(RAIZ, "data", "evidencia_ejecucion.json")

CAMPOS_RED = ("usuarios", "relaciones", "eventos")


def cargar_red(ruta=RUTA_RED):
    """Lee y valida el JSON de la red. Lanza ValueError con un mensaje claro."""
    if not os.path.exists(ruta):
        raise ValueError(f"No se encontró el archivo {ruta}.")
    try:
        with open(ruta, encoding="utf-8") as f:
            red = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"El archivo no es un JSON válido (línea {e.lineno}).")
    faltan = [c for c in CAMPOS_RED if c not in red]
    if faltan:
        raise ValueError(f"Al JSON le faltan los campos: {', '.join(faltan)}.")
    return red


def leer_catalogo(ruta=RUTA_RED):
    """-> lista de (id_video, nombre, popularidad)"""
    return [(j["id"], j["nombre"], j["popularidad"]) for j in cargar_red(ruta).get("catalogo", [])]


def leer_reportes(ruta=RUTA_REPORTES):
    with open(ruta, encoding="utf-8") as f:
        return [Reporte(r["id_reporte"], r["gravedad"], r["descripcion"]) for r in json.load(f)]


def guardar_orden_atencion(filas, ruta=RUTA_ORDEN):
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(filas, f, ensure_ascii=False, indent=2)
    return ruta


def guardar_evidencia(registro, ruta=RUTA_EVIDENCIA):
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(registro, f, ensure_ascii=False, indent=2)
    return ruta
