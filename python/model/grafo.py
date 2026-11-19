"""
MODELO - TDA Grafo (lista de adyacencia) con BFS, DFS, Dijkstra, Floyd-Warshall
y los 4 retos del Parcial de Corte 2.
Tomado de parcial_c2_grafos.py. Aqui NO hay print() ni HTML: solo datos.
"""


class Vertice:
    def __init__(self, id_vertice, nombre, **datos):
        self.id = id_vertice
        self.nombre = nombre
        self.datos = datos          # localidad, juego, coordenadas... (opcional)

    def __repr__(self):
        return self.nombre


class Grafo:
    """Lista de Adyacencia: self.adyacencia[id] = [(vecino, peso), ...]
    self.capacidad[(a,b)] = capacidad maxima de esa arista (Reto 1)."""

    def __init__(self, dirigido=True):
        self.vertices = {}
        self.adyacencia = {}
        self.capacidad = {}
        self.dirigido = dirigido

    def AñadirVertice(self, v):
        self.vertices[v.id] = v
        self.adyacencia.setdefault(v.id, [])

    def BorrarVertice(self, id_v):
        if id_v not in self.vertices:
            return False
        del self.vertices[id_v]
        del self.adyacencia[id_v]
        for lista in self.adyacencia.values():
            lista[:] = [(v, p) for v, p in lista if v != id_v]
        self.capacidad = {k: c for k, c in self.capacidad.items() if id_v not in k}
        return True

    def _set(self, a, b, peso):
        for i, (v, _) in enumerate(self.adyacencia[a]):
            if v == b:
                self.adyacencia[a][i] = (b, peso)
                return
        self.adyacencia[a].append((b, peso))

    def Union(self, a, b, peso=1, capacidad=None):
        if a not in self.vertices or b not in self.vertices:
            return False
        self._set(a, b, peso)
        self.capacidad[(a, b)] = capacidad if capacidad is not None else peso
        if not self.dirigido:
            self._set(b, a, peso)
            self.capacidad[(b, a)] = capacidad if capacidad is not None else peso
        return True

    def BorrarArco(self, a, b):
        if a not in self.adyacencia:
            return False
        antes = len(self.adyacencia[a])
        self.adyacencia[a] = [(v, p) for v, p in self.adyacencia[a] if v != b]
        self.capacidad.pop((a, b), None)
        if not self.dirigido:
            self.adyacencia[b] = [(v, p) for v, p in self.adyacencia[b] if v != a]
            self.capacidad.pop((b, a), None)
        return len(self.adyacencia[a]) < antes

    def EsAdyacente(self, a, b):
        return any(v == b for v, _ in self.adyacencia.get(a, []))

    def GradoSalida(self, id_v):
        return len(self.adyacencia.get(id_v, []))

    def GradoEntrada(self, id_v):
        return sum(1 for lista in self.adyacencia.values() for v, _ in lista if v == id_v)

    def CalcularGrado(self, id_v):
        if self.dirigido:
            return self.GradoEntrada(id_v) + self.GradoSalida(id_v)
        bucle = any(v == id_v for v, _ in self.adyacencia.get(id_v, []))
        return self.GradoSalida(id_v) + (1 if bucle else 0)

    def RecorridoAnchura(self, inicio, excluido=None):
        """BFS normal. Si 'excluido' se da, ese nodo se trata como si no
        existiera (sin borrarlo de verdad) -> usado por el Reto 2."""
        if inicio == excluido:
            return []
        visitados, orden, cola = {inicio}, [inicio], [inicio]
        while cola:
            actual = cola.pop(0)
            for vecino, _ in self.adyacencia[actual]:
                if vecino != excluido and vecino not in visitados:
                    visitados.add(vecino)
                    orden.append(vecino)
                    cola.append(vecino)
        return orden

    def RecorridoProfundidad(self, inicio):
        visitados, orden = set(), []

        def dfs(actual):
            visitados.add(actual)
            orden.append(actual)
            for vecino, _ in self.adyacencia[actual]:
                if vecino not in visitados:
                    dfs(vecino)

        dfs(inicio)
        return [self.vertices[i] for i in orden]

    def Dijkstra(self, origen):
        """Fuente unica, pesos >= 0 (version base, heredada del Taller 2)."""
        D = {v: float("inf") for v in self.vertices}
        P = {v: None for v in self.vertices}
        D[origen] = 0
        visitados = set()
        while len(visitados) < len(self.vertices):
            candidatos = [(D[v], v) for v in self.vertices if v not in visitados and D[v] < float("inf")]
            if not candidatos:
                break
            _, actual = min(candidatos)
            visitados.add(actual)
            for vecino, peso in self.adyacencia[actual]:
                if peso < 0:
                    raise ValueError("Dijkstra no admite pesos negativos")
                if D[actual] + peso < D[vecino]:
                    D[vecino] = D[actual] + peso
                    P[vecino] = actual
        return D, P

    def FloydWarshall(self):
        """Todos los pares, admite pesos negativos (version base, Taller 2)."""
        ids = list(self.vertices.keys())
        idx = {id_: i for i, id_ in enumerate(ids)}
        n = len(ids)
        INF = float("inf")
        D = [[INF] * n for _ in range(n)]
        Pi = [[None] * n for _ in range(n)]
        for i in range(n):
            D[i][i] = 0
        for a, lista in self.adyacencia.items():
            for b, peso in lista:
                D[idx[a]][idx[b]] = peso
                Pi[idx[a]][idx[b]] = a
        for k in range(n):
            for i in range(n):
                for j in range(n):
                    if D[i][k] + D[k][j] < D[i][j]:
                        D[i][j] = D[i][k] + D[k][j]
                        Pi[i][j] = Pi[k][j]
        ciclos_negativos = [ids[i] for i in range(n) if D[i][i] < 0]
        return ids, D, Pi, ciclos_negativos

    # ========================================================
    # RETO 1 [30%]: Enrutamiento Multicriterio con Cuello de
    # Botella (Min-Max Capacity Path / "widest path")
    # ========================================================
    def RutaMayorCapacidad(self, origen, destino):
        """Devuelve (ruta, capacidadCuelloBotella).
        En vez de SUMAR pesos como Dijkstra clasico, propaga el MINIMO
        de capacidad visto en el camino, y en cada paso avanza por el
        nodo con mayor capacidad acumulada (voraz, igual que Dijkstra
        pero invirtiendo min<->max y suma<->minimo)."""
        if origen not in self.vertices or destino not in self.vertices:
            return [], 0.0

        cap = {v: float("-inf") for v in self.vertices}
        P = {v: None for v in self.vertices}
        cap[origen] = float("inf")   # <- el origen no tiene cuello de botella todavia
        visitados = set()

        while len(visitados) < len(self.vertices):
            candidatos = [(cap[v], v) for v in self.vertices if v not in visitados and cap[v] > float("-inf")]
            if not candidatos:
                break
            _, actual = max(candidatos)    # <- AQUI ESTA LO VORAZ: se cierra el nodo con MAYOR capacidad (no menor)
            visitados.add(actual)
            if actual == destino:
                break
            for vecino, peso in self.adyacencia[actual]:
                c_arista = self.capacidad.get((actual, vecino), peso)
                candidato = min(cap[actual], c_arista)   # <- AQUI EL CUELLO DE BOTELLA: la capacidad de la ruta es el MINIMO de sus tramos
                if candidato > cap[vecino]:
                    cap[vecino] = candidato              # <- AQUI SE RELAJA: se guarda la mejor capacidad vista hasta el vecino
                    P[vecino] = actual

        if cap[destino] == float("-inf"):
            return [], 0.0
        ruta = reconstruir_camino(P, destino)
        return ruta, cap[destino]

    # ========================================================
    # RETO 2 [30%]: Diagnostico Automatico de Puntos Criticos
    # de Falla (Stress Testing / cut-vertices)
    # ========================================================
    def DetectarPuntosCriticosDeFalla(self, referencia=None):
        """Devuelve la lista de Vertices cuya caida desconecta la red
        (medido como alcanzabilidad desde 'referencia' via BFS).
        No destructivo: nunca borra nada del grafo real, solo usa la
        mascara 'excluido' de RecorridoAnchura."""
        if referencia is None:
            referencia = next(iter(self.vertices))

        base = set(self.RecorridoAnchura(referencia))   # <- conectividad original, sin tocar nada
        criticos = []

        for v in self.vertices:
            if v == referencia:
                continue
            alcanzables_sin_v = set(self.RecorridoAnchura(referencia, excluido=v))  # <- simulacion de caida (temporal, no destructiva)
            esperados = base - {v}
            perdidos = esperados - alcanzables_sin_v   # <- nodos que SI eran alcanzables y dejaron de serlo
            if perdidos:
                criticos.append((self.vertices[v], sorted(perdidos)))

        return criticos

    # ========================================================
    # RETO 3 [25%]: Dijkstra K-Alternativo (ruta de respaldo
    # disjunta en aristas)
    # ========================================================
    def GenerarRutaConRespaldo(self, origen, destino):
        """1) Dijkstra normal -> ruta primaria.
        2) Inhabilita (BorrarArco) solo las aristas de esa ruta.
        3) Dijkstra de nuevo -> ruta de respaldo.
        4) Restaura el grafo exactamente como estaba.
        Devuelve un dict con ambas rutas, costos y % de diferencia."""
        D, P = self.Dijkstra(origen)
        if D[destino] == float("inf"):
            return {"alerta": f"No existe ninguna ruta entre {origen} y {destino} (ni primaria)."}

        ruta_primaria = reconstruir_camino(P, destino)
        costo_primaria = D[destino]
        aristas_primarias = list(zip(ruta_primaria, ruta_primaria[1:]))

        # <- AQUI SE GUARDA EL ESTADO (gestion de resiliencia / copia de respaldo)
        respaldo_estado = {(a, b): peso for a, lista in self.adyacencia.items()
                            for b, peso in lista if (a, b) in aristas_primarias}
        respaldo_capacidad = {ab: self.capacidad.get(ab) for ab in aristas_primarias}

        for a, b in aristas_primarias:
            self.BorrarArco(a, b)   # <- AQUI SE INHABILITA temporalmente (no se borra el vertice, solo el arco)

        D2, P2 = self.Dijkstra(origen)

        # <- AQUI SE RESTAURA el grafo exactamente como estaba, pase lo que pase
        for (a, b), peso in respaldo_estado.items():
            self.Union(a, b, peso, capacidad=respaldo_capacidad.get((a, b)))

        if D2[destino] == float("inf"):
            return {
                "alerta": "Red no redundante entre origen y destino",
                "ruta_primaria": ruta_primaria,
                "costo_primaria": costo_primaria,
            }

        ruta_respaldo = reconstruir_camino(P2, destino)
        costo_respaldo = D2[destino]
        diferencia_pct = ((costo_respaldo - costo_primaria) / costo_primaria) * 100 if costo_primaria else 0.0

        return {
            "ruta_primaria": ruta_primaria,
            "costo_primaria": costo_primaria,
            "ruta_respaldo": ruta_respaldo,
            "costo_respaldo": costo_respaldo,
            "diferencia_pct": diferencia_pct,
        }


def reconstruir_camino(P, destino):
    camino = [destino]
    while P[camino[-1]] is not None:
        camino.append(P[camino[-1]])
    return list(reversed(camino))


# ========================================================
# RETO 4: auditoria de la diagonal de Floyd-Warshall
# (funcion de modulo: solo recibe la matriz ya calculada)
# ========================================================
def detectar_anomalia_ciclo_negativo(matriz, ids=None):
    """Devuelve la lista de (nodo, D[i][i]) con D[i][i] < 0.
    Lista vacia = sin ciclos negativos."""
    return [(ids[i] if ids else i, matriz[i][i])
            for i in range(len(matriz)) if matriz[i][i] < 0]


ACCIONES_CICLO_NEGATIVO = [
    "Congelar la promoción o el arco con peso negativo (aquí U3 → U1 = −30).",
    "Poner un tope: ningún peso puede ser menor que 0, o limitar cuántas veces se puede cobrar el incentivo por usuario.",
    "Revisar con Floyd-Warshall cada vez que se cargue una promoción, antes de publicarla.",
    "No usar Dijkstra sobre ese grafo: con pesos negativos sus resultados no son confiables.",
]


# ========================================================
# Construccion del grafo social de Gamefolks
# ========================================================
USUARIOS = [
    ("U1", "Juana_Gamer"), ("U2", "Camilo92"), ("U3", "Valentina_Streams"),
    ("U4", "AndresPlay"), ("U5", "SofiaGG"), ("U6", "MateoRush"),
    ("U7", "LauraFPS"), ("U8", "NicoBuilds"), ("U9", "CamilaRPG"),
    ("U10", "DiegoSpeedrun"),
]

# (origen, destino, peso=interacciones/semana, capacidad=ancho de banda)
RELACIONES = [
    ("U1", "U2", 8, 12), ("U2", "U3", 15, 20), ("U3", "U1", 5, 6),
    ("U4", "U3", 12, 9), ("U5", "U3", 9, 14), ("U6", "U3", 6, 5),
    ("U7", "U3", 10, 18), ("U3", "U8", 4, 7), ("U8", "U4", 7, 10),
    ("U9", "U10", 11, 16), ("U10", "U9", 11, 16), ("U1", "U3", 6, 25),
    ("U2", "U8", 5, 3), ("U3", "U2", 3, 22),
]


def construir_grafo_gamefolks():
    g = Grafo(dirigido=True)
    for id_, nombre in USUARIOS:
        g.AñadirVertice(Vertice(id_, nombre))
    for a, b, peso, cap in RELACIONES:
        g.Union(a, b, peso, capacidad=cap)
    return g


def construir_grafo_con_promocion():
    """Mismo grafo, pero la promocion hace U3 -> U1 = -30 (ciclo negativo)."""
    g = construir_grafo_gamefolks()
    g.Union("U3", "U1", -30, capacidad=g.capacidad.get(("U3", "U1")))
    return g


def construir_grafo_desde_red(red):
    """Arma el grafo a partir del diccionario leido de data/red_gamefolks.json.
    Lanza ValueError si una relacion apunta a un usuario que no existe."""
    g = Grafo(dirigido=True)
    for u in red["usuarios"]:
        extra = {k: v for k, v in u.items() if k not in ("id", "usuario")}
        g.AñadirVertice(Vertice(u["id"], u["usuario"], **extra))
    for r in red["relaciones"]:
        if not g.Union(r["origen"], r["destino"], r["peso"], capacidad=r.get("capacidad")):
            raise ValueError(f"Relación inválida: {r['origen']} -> {r['destino']} (usuario inexistente).")
    return g
