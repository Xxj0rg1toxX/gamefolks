"""
MODELO - Vertex Cover (cobertura de vertices) sobre la red social.
Elegir pocos usuarios a monitorear para que TODA interaccion tenga
al menos un extremo vigilado. La direccion de "sigue a" se ignora.
"""
from itertools import combinations


def aristas_sin_direccion(grafo):
    """Del Grafo dirigido saca las interacciones unicas (u, v) sin direccion."""
    vistas, resultado = set(), []
    for a, lista in grafo.adyacencia.items():
        for b, _ in lista:
            par = frozenset((a, b))
            if a != b and par not in vistas:
                vistas.add(par)
                resultado.append((a, b))
    return resultado


def cobertura_aproximada(aristas):
    """Tome una arista sin cubrir, meta AMBOS extremos, y repita.
    Garantia: nunca usa mas del doble del optimo (2-aproximacion)."""
    cubiertos = set()
    elegidas = []
    for u, v in aristas:
        if u not in cubiertos and v not in cubiertos:
            elegidas.append((u, v))
            cubiertos.add(u)
            cubiertos.add(v)
    return cubiertos, elegidas


def cobertura_voraz_por_grado(aristas):
    """Voraz: siempre vigila al usuario que cubre MAS aristas pendientes."""
    pendientes = list(aristas)
    cubiertos = []
    while pendientes:
        grados = {}
        for u, v in pendientes:
            grados[u] = grados.get(u, 0) + 1
            grados[v] = grados.get(v, 0) + 1
        mejor = max(grados, key=lambda x: grados[x])
        cubiertos.append(mejor)
        pendientes = [(u, v) for u, v in pendientes if mejor not in (u, v)]
    return set(cubiertos)


def cobertura_optima(aristas):
    """Fuerza bruta (solo sirve en grafos chicos): prueba todos los subconjuntos."""
    nodos = sorted({x for a in aristas for x in a})
    for k in range(1, len(nodos) + 1):
        for subconjunto in combinations(nodos, k):
            if es_cobertura(aristas, set(subconjunto)):
                return set(subconjunto)


def es_cobertura(aristas, cubiertos):
    return all(u in cubiertos or v in cubiertos for u, v in aristas)
