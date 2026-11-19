"""
WEB - Servicios: puente entre el almacén de datos y el MODELO del curso.
Cada función lee el almacén, arma la estructura propia (Grafo, Trie, MaxHeap,
grafo de conflictos...) y corre el algoritmo. Es el mismo código de la versión Flask,
solo que en vez de consultas SQL lee listas y diccionarios (ver almacen.py).
"""
import json
import math
import os
from datetime import datetime

from model.grafo import Grafo, Vertice
from model import busqueda as bus
from model import coloracion as col
from model import tsp as tsp_mod
from model import vertex_cover as vc
from model.trie import Trie
from model.heap import MaxHeap, Reporte

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Coordenadas aproximadas (centro de cada localidad de Bogota) para la ruta de premios
LOCALIDADES = {
    "Usaquén": (4.7030, -74.0300), "Chapinero": (4.6486, -74.0628), "Santa Fe": (4.6000, -74.0700),
    "San Cristóbal": (4.5700, -74.0900), "Usme": (4.4800, -74.1200), "Tunjuelito": (4.5750, -74.1350),
    "Bosa": (4.6150, -74.1860), "Kennedy": (4.6300, -74.1530), "Fontibón": (4.6780, -74.1420),
    "Engativá": (4.7090, -74.1120), "Suba": (4.7410, -74.0840), "Barrios Unidos": (4.6680, -74.0760),
    "Teusaquillo": (4.6440, -74.0930), "Los Mártires": (4.6060, -74.0900), "Antonio Nariño": (4.5900, -74.1000),
    "Puente Aranda": (4.6150, -74.1150), "La Candelaria": (4.5960, -74.0730), "Rafael Uribe Uribe": (4.5730, -74.1150),
    "Ciudad Bolívar": (4.5100, -74.1500),
}
SERVIDORES = [f"S-LATAM-{i}" for i in range(1, 8)]
MOTIVOS = {"Discurso de odio": 90, "Contenido violento": 85, "Acoso o bullying": 80, "Suplantación": 70,
           "Spam o estafa": 60, "Otro": 30, "Spoilers sin aviso": 20}
FRANJA_INICIO, FRANJA_MINUTOS = 18 * 60, 90          # turno 1 = 6:00 pm, cada turno dura 1 h 30 min
BODEGA = {"nombre": "Bodega Gamefolks", "localidad": "Chapinero", "lat": 4.6486, "lon": -74.0628}
MAX_OPTIMO_VC = 16


def _catalogo():
    with open(os.path.join(RAIZ, "data", "red_gamefolks.json"), encoding="utf-8") as f:
        return json.load(f)["catalogo"]


def _usuarios(con):
    return {u["id"]: dict(u) for u in con.usuarios_ordenados()}


def grafo_desde_db(con):
    """Grafo DIRIGIDO 'sigue a' con lista de adyacencia propia (model.grafo.Grafo)."""
    g = Grafo(dirigido=True)
    for u in _usuarios(con).values():
        g.AñadirVertice(Vertice(u["id"], u["usuario"], juego=u["juego"], localidad=u["localidad"],
                                lat=u["lat"], lon=u["lon"], x=u["x"], y=u["y"]))
    for r in con.seguimientos:
        g.Union(r["origen"], r["destino"], r["peso"], capacidad=r["capacidad"])
    return g


def _mini(g, i):
    v = g.vertices[i]
    return {"id": i, "usuario": v.nombre, "juego": v.datos.get("juego", "")}


# ---------------------------------------------------------------- BFS
def sugerencias(con, yo, cuantas=6):
    g = grafo_desde_db(con)
    niveles, padre = bus.bfs_niveles(g.adyacencia, yo, max_nivel=3, con_padres=True)
    sigo = {v for v, _ in g.adyacencia[yo]}
    salida = []
    for nivel in (2, 3):
        for i in niveles.get(nivel, []):
            if i != yo and i not in sigo:
                medio = padre[i]
                while padre[medio] != yo and padre[medio] is not None:
                    medio = padre[medio]
                salida.append({**_mini(g, i), "nivel": nivel, "por_medio_de": g.vertices[padre[i]].nombre,
                               "amigo_directo": g.vertices[medio].nombre})
    if len(salida) < cuantas:                           # relleno: los mas seguidos que aun no sigo
        ya = {s["id"] for s in salida} | sigo | {yo}
        populares = sorted((i for i in g.vertices if i not in ya), key=lambda i: -g.GradoEntrada(i))
        salida += [{**_mini(g, i), "nivel": None, "por_medio_de": None, "amigo_directo": None,
                    "seguidores": g.GradoEntrada(i)} for i in populares]
    return {"niveles": {k: [_mini(g, i) for i in v] for k, v in niveles.items()}, "sugerencias": salida[:cuantas]}


# ---------------------------------------------------------------- UCS + BFS
def ruta(con, yo, hasta):
    g = grafo_desde_db(con)
    if hasta not in g.vertices:
        raise ValueError("Ese usuario no existe.")
    if hasta == yo:
        raise ValueError("Elige a otra persona: esa ruta eres tú.")
    salida = {}
    for alg in ("UCS", "BFS"):
        r = bus.ALGORITMOS[alg](g.adyacencia, yo, hasta)
        tramos = [{"desde": g.vertices[a].nombre, "hasta": g.vertices[b].nombre, "costo": dict(g.adyacencia[a])[b]}
                  for a, b in zip(r["camino"], r["camino"][1:])] if r["camino"] else []
        salida[alg] = {"camino": [_mini(g, i) for i in r["camino"]] if r["camino"] else None, "costo": r["costo"],
                       "saltos": r["saltos"], "expandidos": len(r["expandidos"]), "tramos": tramos}
    return salida


# ---------------------------------------------------------------- DFS
def ciclos(con, yo):
    g = grafo_desde_db(con)
    todos = bus.detectar_ciclos_dfs(g.adyacencia)
    mios = [c for c in todos if yo in c]
    return {"mios": [[g.vertices[i].nombre for i in c] for c in mios],
            "total": len(todos), "todos": [[g.vertices[i].nombre for i in c] for c in todos]}


# ---------------------------------------------------------------- Trie
def buscar(con, q):
    q = (q or "").strip()
    if len(q) < 2:
        return {"usuarios": [], "juegos": []}
    g = grafo_desde_db(con)
    t_usuarios, por_nombre = Trie(), {}
    for i, v in g.vertices.items():
        t_usuarios.insertar(v.nombre, g.GradoEntrada(i))
        por_nombre[v.nombre] = i
    t_juegos = Trie()
    for juego in _catalogo():
        t_juegos.insertar(juego["nombre"], juego["popularidad"])
    usuarios = [{**_mini(g, por_nombre[n]), "seguidores": p} for n, p in t_usuarios.autocompletar_top_k(q, 5)]
    juegos = [{"nombre": n, "popularidad": p} for n, p in t_juegos.autocompletar_top_k(q, 5)]
    return {"usuarios": usuarios, "juegos": juegos}


def juegos_populares(cuantos=6):
    return sorted(_catalogo(), key=lambda j: -j["popularidad"])[:cuantos]


# ---------------------------------------------------------------- Welsh-Powell
def _eventos(con):
    return {e["id"]: {**e, "participantes": [u for ev, u in con.participantes if ev == e["id"]]}
            for e in con.eventos_ordenados()}


def _hora(minutos):
    h, m = divmod(minutos, 60)
    sufijo = "pm" if h >= 12 else "am"
    return f"{(h - 1) % 12 + 1}:{m:02d} {sufijo}"


def horario_eventos(con):
    eventos = _eventos(con)
    usuarios = _usuarios(con)
    nombres = {i: u["usuario"] for i, u in usuarios.items()}
    lista = [{"id": e["id"], "nombre": e["nombre"], "juego": e["juego"], "servidor": e["servidor"],
              "participantes": [nombres.get(p, p) for p in e["participantes"]]} for e in eventos.values()]
    if not eventos:
        return {"eventos": [], "turnos": [], "n_turnos": 0, "conflictos": []}
    grafo = col.construir_grafo_conflictos(eventos)
    grados = col.calcular_grados(grafo)
    orden = col.ordenar_por_grado(grados)
    color = col.welsh_powell(grafo, orden)
    turnos = []
    for t, evs in col.agrupar_por_turno(color).items():
        ini = FRANJA_INICIO + (t - 1) * FRANJA_MINUTOS
        turnos.append({"turno": t, "inicio": _hora(ini), "fin": _hora(ini + FRANJA_MINUTOS),
                       "eventos": [{"id": e, "nombre": eventos[e]["nombre"]} for e in evs]})
    for e in lista:
        e["grado"], e["turno"] = grados[e["id"]], color[e["id"]]
    conflictos = [{"a": a, "b": b, "motivo": col.motivo_conflicto(eventos, a, b, nombres)}
                  for a in grafo for b in grafo[a] if a < b]
    return {"eventos": lista, "turnos": turnos, "n_turnos": max(color.values()), "orden": orden,
            "valida": col.es_coloracion_valida(grafo, color), "conflictos": conflictos}


def crear_evento(con, creador, nombre, juego, servidor, participantes):
    nombre = (nombre or "").strip()
    if not nombre:
        raise ValueError("El evento necesita un nombre.")
    if servidor not in SERVIDORES:
        raise ValueError("Elige un servidor de la lista.")
    usuarios = _usuarios(con)
    participantes = list(dict.fromkeys(p for p in participantes if p in usuarios))
    if not participantes:
        raise ValueError("Elige al menos un participante.")
    eid = con.siguiente_id_evento()
    con.eventos[eid] = {"id": eid, "nombre": nombre[:60], "juego": (juego or "").strip()[:40],
                        "servidor": servidor, "creador": creador}
    con.participantes.extend([eid, p] for p in participantes)
    return eid


# ---------------------------------------------------------------- TSP
def premios(con, ganadores):
    usuarios = _usuarios(con)
    ganadores = list(dict.fromkeys(g for g in ganadores if g in usuarios))
    if not ganadores:
        raise ValueError("Elige al menos un ganador.")
    sin_ubicacion = [usuarios[g]["usuario"] for g in ganadores if usuarios[g]["lat"] is None]
    if sin_ubicacion:
        raise ValueError(f"Estos usuarios no tienen localidad: {', '.join(sin_ubicacion)}.")
    puntos = [("BODEGA", BODEGA["lat"], BODEGA["lon"])] + [(g, usuarios[g]["lat"], usuarios[g]["lon"]) for g in ganadores]
    d = tsp_mod.matriz_distancias(puntos)
    ids = [p[0] for p in puntos]
    aprox = tsp_mod.tsp_aproximado_mst(ids, d)
    try:
        exacto = tsp_mod.tsp_exacto(ids, d)
    except ValueError:
        exacto = None

    def info(i):
        if i == "BODEGA":
            return {"id": i, "nombre": BODEGA["nombre"], "localidad": BODEGA["localidad"], "lat": BODEGA["lat"], "lon": BODEGA["lon"]}
        u = usuarios[i]
        return {"id": i, "nombre": u["usuario"], "localidad": u["localidad"], "lat": u["lat"], "lon": u["lon"]}

    return {"puntos": [info(i) for i in ids],
            "aprox": {"ruta": aprox["ruta"], "km": aprox["costo"], "mst": [[a, b] for a, b, _ in aprox["aristas_mst"]],
                      "km_mst": aprox["peso_mst"]},
            "exacto": {"ruta": exacto["ruta"], "km": exacto["costo"], "probadas": exacto["rutas_probadas"]} if exacto else None,
            "razon": round(aprox["costo"] / exacto["costo"], 3) if exacto and exacto["costo"] else None,
            "tramos": [{"desde": info(a)["nombre"], "hasta": info(b)["nombre"], "km": d[(a, b)]}
                       for a, b in zip(aprox["ruta"], aprox["ruta"][1:])]}


# ---------------------------------------------------------------- Heap (moderacion)
def _heap_pendientes(con):
    """Prioridad = gravedad del motivo + 5 puntos por cada dia pendiente (envejecimiento)."""
    heap, info = MaxHeap(), {}
    ahora = datetime.now()
    reportes = []
    for r in con.reportes:
        pub = con.publicacion(r["publicacion"])
        if r["estado"] != "pendiente" or not pub:
            continue
        dias = (ahora - datetime.fromisoformat(r["creado"])).days
        prioridad = r["gravedad"] + 5 * dias
        reportes.append(Reporte(str(r["id"]), prioridad, r["motivo"]))
        info[str(r["id"])] = {"id": r["id"], "motivo": r["motivo"], "gravedad": r["gravedad"], "dias": dias,
                              "prioridad": prioridad, "publicacion": r["publicacion"], "texto": pub["texto"],
                              "autor": con.usuarios[pub["autor"]]["usuario"],
                              "reportero": con.usuarios[r["reportero"]]["usuario"]}
    heap.construir_heap(reportes)
    return heap, info


def cola_moderacion(con):
    heap, info = _heap_pendientes(con)
    orden = []
    while not heap.esta_vacio():                       # extraer todo = orden de atencion (heap sort)
        orden.append(info[heap.extraer_max().id_reporte])
    return orden


def atender_siguiente(con, accion):
    if accion not in ("eliminar", "descartar"):
        raise ValueError("Acción no válida.")
    heap, info = _heap_pendientes(con)
    r = heap.extraer_max()
    if r is None:
        raise ValueError("No hay reportes pendientes. 🎉")
    dato = info[r.id_reporte]
    if accion == "eliminar":
        for rep in con.reportes:
            if rep["publicacion"] == dato["publicacion"]:
                rep["estado"] = "atendido"
        con.borrar_publicacion(dato["publicacion"])
    else:
        for rep in con.reportes:
            if rep["id"] == dato["id"]:
                rep["estado"] = "atendido"
    return dato


# ---------------------------------------------------------------- Vertex Cover
def monitorear(con):
    g = grafo_desde_db(con)
    aristas = vc.aristas_sin_direccion(g)
    if not aristas:
        return {"aprox": [], "elegidas": [], "optimo": None, "interacciones": 0}
    aprox, elegidas = vc.cobertura_aproximada(aristas)
    nodos = {x for a in aristas for x in a}
    optimo = vc.cobertura_optima(aristas) if len(nodos) <= MAX_OPTIMO_VC else None
    nom = lambda i: g.vertices[i].nombre
    return {"interacciones": len(aristas), "aprox": sorted(nom(i) for i in aprox),
            "elegidas": [[nom(u), nom(v)] for u, v in elegidas],
            "optimo": sorted(nom(i) for i in optimo) if optimo is not None else None,
            "valida": vc.es_cobertura(aristas, aprox)}


# ---------------------------------------------------------------- red para dibujar
def red(con):
    g = grafo_desde_db(con)
    sin_pos = [i for i, v in g.vertices.items() if v.datos.get("x") is None]
    nodos = []
    for i, v in g.vertices.items():
        x, y = v.datos.get("x"), v.datos.get("y")
        if x is None:                                   # usuarios nuevos: en un circulo alrededor
            k = sin_pos.index(i)
            ang = 2 * math.pi * k / max(1, len(sin_pos))
            x, y = 430 + 390 * math.cos(ang), 400 + 330 * math.sin(ang)
        nodos.append({"id": i, "usuario": v.nombre, "x": x, "y": y})
    aristas = [{"a": a, "b": b, "peso": p} for a, lista in g.adyacencia.items() for b, p in lista]
    return {"nodos": nodos, "aristas": aristas}
