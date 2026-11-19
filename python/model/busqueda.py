"""
MODELO - Busqueda no informada sobre el grafo social: BFS, DFS y UCS.
Tomado de busqueda_gamefolks.py. Recibe una lista de adyacencia
{estado: [(vecino, costo), ...]} (la misma que usa el TDA Grafo).
"""
import heapq
from collections import deque


def _reconstruir(padre, meta):
    camino = [meta]
    while padre[camino[-1]] is not None:
        camino.append(padre[camino[-1]])
    return camino[::-1]


def _costo(grafo, camino):
    return sum(dict(grafo[a])[b] for a, b in zip(camino, camino[1:]))


def _resultado(grafo, camino, expandidos, generados, fmax):
    return {
        "camino": camino,
        "saltos": len(camino) - 1 if camino else None,
        "costo": _costo(grafo, camino) if camino else None,
        "expandidos": expandidos,
        "generados": generados,
        "frontera_max": fmax,
    }


def bfs(grafo, inicio, meta):
    frontera = deque([inicio])
    padre = {inicio: None}
    expandidos, generados, fmax = [], 1, 1
    while frontera:
        actual = frontera.popleft()
        expandidos.append(actual)
        if actual == meta:
            return _resultado(grafo, _reconstruir(padre, meta), expandidos, generados, fmax)
        for vecino, _ in grafo[actual]:
            if vecino not in padre:
                padre[vecino] = actual
                frontera.append(vecino)
                generados += 1
        fmax = max(fmax, len(frontera))
    return _resultado(grafo, None, expandidos, generados, fmax)


def dfs(grafo, inicio, meta):
    frontera = [(inicio, None)]
    padre, explorados = {}, set()
    expandidos, generados, fmax = [], 1, 1
    while frontera:
        actual, de = frontera.pop()
        if actual in explorados:
            continue
        explorados.add(actual)
        padre[actual] = de
        expandidos.append(actual)
        if actual == meta:
            return _resultado(grafo, _reconstruir(padre, meta), expandidos, generados, fmax)
        for vecino, _ in reversed(grafo[actual]):
            if vecino not in explorados:
                frontera.append((vecino, actual))
                generados += 1
        fmax = max(fmax, len(frontera))
    return _resultado(grafo, None, expandidos, generados, fmax)


def ucs(grafo, inicio, meta):
    frontera = [(0, 0, inicio)]
    mejor, padre, explorados = {inicio: 0}, {inicio: None}, set()
    expandidos, generados, fmax, orden = [], 1, 1, 1
    while frontera:
        g, _, actual = heapq.heappop(frontera)
        if actual in explorados:
            continue
        explorados.add(actual)
        expandidos.append(actual)
        if actual == meta:             # la meta se prueba AL SACAR
            return _resultado(grafo, _reconstruir(padre, meta), expandidos, generados, fmax)
        for vecino, costo in grafo[actual]:
            nuevo = g + costo
            if vecino not in mejor or nuevo < mejor[vecino]:
                mejor[vecino] = nuevo
                padre[vecino] = actual
                heapq.heappush(frontera, (nuevo, orden, vecino))
                orden += 1
                generados += 1
        fmax = max(fmax, len(frontera))
    return _resultado(grafo, None, expandidos, generados, fmax)


ALGORITMOS = {"BFS": bfs, "DFS": dfs, "UCS": ucs}


# ===================================================================
# Consultas operativas del Parcial C3 (Modulo 2)
# ===================================================================
def bfs_niveles(grafo, inicio, max_nivel=3, con_padres=False):
    """BFS por niveles: {nivel: [usuarios]}. Nivel 1 = a quien sigue,
    nivel 2 = a quien siguen ellos (sugerencias de amistad), etc.
    Con con_padres=True tambien devuelve {usuario: por medio de quien se llego}."""
    if inicio not in grafo:
        raise ValueError(f"No existe el usuario {inicio}.")
    nivel_de = {inicio: 0}
    padre = {inicio: None}
    cola = deque([inicio])
    niveles = {}
    while cola:
        actual = cola.popleft()
        if nivel_de[actual] == max_nivel:
            continue
        for vecino, _ in grafo[actual]:
            if vecino not in nivel_de:
                nivel_de[vecino] = nivel_de[actual] + 1
                padre[vecino] = actual
                niveles.setdefault(nivel_de[vecino], []).append(vecino)
                cola.append(vecino)
    return (niveles, padre) if con_padres else niveles


def detectar_ciclos_dfs(grafo):
    """DFS con 3 colores (blanco = sin visitar, gris = en la pila, negro = terminado).
    Si desde un nodo gris llegamos a otro nodo gris, encontramos un ciclo.
    Devuelve la lista de ciclos distintos encontrados (cada uno como lista de ids)."""
    BLANCO, GRIS, NEGRO = 0, 1, 2
    color = {v: BLANCO for v in grafo}
    pila = []
    ciclos, vistos = [], set()

    def visitar(u):
        color[u] = GRIS
        pila.append(u)
        for v, _ in grafo[u]:
            if color[v] == GRIS:                     # arco de retroceso = ciclo
                ciclo = pila[pila.index(v):] + [v]
                clave = frozenset(ciclo)
                if clave not in vistos:
                    vistos.add(clave)
                    ciclos.append(ciclo)
            elif color[v] == BLANCO:
                visitar(v)
        pila.pop()
        color[u] = NEGRO

    for v in grafo:
        if color[v] == BLANCO:
            visitar(v)
    return ciclos
