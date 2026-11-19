"""
MODELO - Problema del Viajero (TSP) para la ruta de reparto de premios.
Un repartidor sale de la Bodega Gamefolks, entrega un kit a cada ganador
y vuelve a la bodega. Distancias en km (formula de haversine).

- tsp_aproximado_mst: Prim (arbol de expansion minima) + recorrido en preorden.
  Garantia: la ruta nunca cuesta mas del DOBLE de la optima.
- tsp_exacto: fuerza bruta (todas las permutaciones). Solo para pocos puntos.
"""
import math
from itertools import permutations

MAX_PUNTOS_EXACTO = 9


def distancia_km(lat1, lon1, lat2, lon2):
    """Distancia en linea recta sobre la Tierra (haversine)."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def matriz_distancias(puntos):
    """puntos = [(id, lat, lon), ...] -> {(a, b): km}"""
    d = {}
    for a, la, lo in puntos:
        for b, lb, lob in puntos:
            d[(a, b)] = 0.0 if a == b else round(distancia_km(la, lo, lb, lob), 2)
    return d


def costo_ruta(ruta, d):
    return round(sum(d[(a, b)] for a, b in zip(ruta, ruta[1:])), 2)


def arbol_expansion_minima(ids, d):
    """Prim con listas (O(n^2)). Devuelve {nodo: [hijos]} con raiz en ids[0]."""
    raiz = ids[0]
    en_arbol = {raiz}
    mejor = {v: (d[(raiz, v)], raiz) for v in ids if v != raiz}
    hijos = {v: [] for v in ids}
    aristas = []
    while mejor:
        v = min(mejor, key=lambda x: mejor[x][0])
        costo, padre = mejor.pop(v)
        en_arbol.add(v)
        hijos[padre].append(v)
        aristas.append((padre, v, costo))
        for w in mejor:
            if d[(v, w)] < mejor[w][0]:
                mejor[w] = (d[(v, w)], v)
    return hijos, aristas


def tsp_aproximado_mst(ids, d):
    """1) arbol minimo, 2) preorden (DFS) del arbol, 3) volver al inicio."""
    if len(ids) < 2:
        raise ValueError("Se necesitan al menos 2 puntos para una ruta.")
    hijos, aristas = arbol_expansion_minima(ids, d)
    ruta = []

    def preorden(v):
        ruta.append(v)                       # si ya lo visitamos, no se repite: atajo
        for h in hijos[v]:
            preorden(h)

    preorden(ids[0])
    ruta.append(ids[0])
    peso_mst = round(sum(c for _, _, c in aristas), 2)
    return {"ruta": ruta, "costo": costo_ruta(ruta, d), "aristas_mst": aristas, "peso_mst": peso_mst}


def tsp_exacto(ids, d):
    """Prueba todos los ordenes posibles (n-1)! con el inicio fijo."""
    if len(ids) - 1 > MAX_PUNTOS_EXACTO:
        raise ValueError(f"La fuerza bruta solo se permite con {MAX_PUNTOS_EXACTO} entregas o menos.")
    inicio, resto = ids[0], ids[1:]
    mejor_ruta, mejor_costo, probadas = None, float("inf"), 0
    for orden in permutations(resto):
        ruta = [inicio, *orden, inicio]
        c = costo_ruta(ruta, d)
        probadas += 1
        if c < mejor_costo:
            mejor_ruta, mejor_costo = ruta, c
    return {"ruta": mejor_ruta, "costo": mejor_costo, "rutas_probadas": probadas}
