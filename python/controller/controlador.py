"""
CONTROLADOR - Conecta la VISTA con los MODELOS.
La vista solo llama a estos metodos y muestra lo que devuelven; no conoce
las estructuras. Los errores de validacion salen como ValueError.
"""
import time

from model.arboles import ArbolBST, ArbolAVL
from model.clasificacion import ArbolBinarioJuegos, ArbolNarioJuegos
from model.arbol_b import ArbolB, ArbolBMas
from model.trie import (Trie, memoria_trie_en_bytes, memoria_lista_en_bytes,
                        memoria_set_en_bytes)
from model.heap import MaxHeap, Reporte
from model.grafo import (construir_grafo_desde_red, reconstruir_camino,
                         detectar_anomalia_ciclo_negativo, ACCIONES_CICLO_NEGATIVO)
from model import tsp as tsp_mod
from model import coloracion as col
from model import busqueda as bus
from model import vertex_cover as vc
from model import datos


def _entero(texto, nombre="valor", minimo=None):
    t = str(texto).strip()
    if not t.lstrip("-").isdigit():
        raise ValueError(f"{nombre} debe ser un número entero.")
    n = int(t)
    if minimo is not None and n < minimo:
        raise ValueError(f"{nombre} debe ser al menos {minimo}.")
    return n


class Controlador:
    def __init__(self):
        self.reiniciar_todo()

    def reiniciar_todo(self):
        # --- Corte 1 ---
        self.bst, self.avl = ArbolBST(), ArbolAVL()
        self.videos_subidos = 0
        self.arbol_bin = ArbolBinarioJuegos()
        self.arbol_nario = ArbolNarioJuegos()
        self._cargar_juegos_ejemplo()
        self.indice_usuarios = ArbolB()
        for id_, nombre in [(1010, "Juana"), (1020, "Camilo"), (1005, "Valentina"),
                            (1006, "Andrés"), (1012, "Sofía"), (1030, "Mateo"),
                            (1007, "Laura"), (1017, "Nicolás")]:
            self.indice_usuarios.insertar(id_, nombre)
        self.indice_tags = ArbolBMas()
        for tag, v in [("Shooter", "V1"), ("Simulacion", "V2"), ("Plataforma", "V3"),
                       ("Shooter", "V4"), ("Accion", "V5"), ("Terror", "V6"),
                       ("Comedia", "V7"), ("Deportes", "V8")]:
            self.indice_tags.indexar_video(tag, v)
        self.recargar_catalogo()
        self.recargar_reportes()
        # --- Corte 2 y Corte 3 (grafos): la red real sale del JSON ---
        self.cargar_red()

    # =============== CARGAR RED (Modulo 1) ===============
    def cargar_red(self, ruta=None):
        """Lee data/red_gamefolks.json (u otra ruta) y arma el grafo."""
        red = datos.cargar_red(ruta) if ruta else datos.cargar_red()
        grafo = construir_grafo_desde_red(red)
        promo = construir_grafo_desde_red(red)
        if "U3" in promo.vertices and "U1" in promo.vertices:
            promo.Union("U3", "U1", -30, capacidad=promo.capacidad.get(("U3", "U1")))
        self.red, self.grafo, self.grafo_promo = red, grafo, promo
        self.eventos = {e["id"]: e for e in red["eventos"]}
        return {"usuarios": len(grafo.vertices),
                "relaciones": sum(len(l) for l in grafo.adyacencia.values()),
                "eventos": len(self.eventos)}

    def resolver_usuario(self, texto):
        """Acepta 'U3', '3' o el nombre de usuario (sin importar mayusculas)."""
        t = str(texto).strip()
        if not t:
            raise ValueError("Escribe un usuario.")
        if t.upper() in self.grafo.vertices:
            return t.upper()
        if t.isdigit() and f"U{t}" in self.grafo.vertices:
            return f"U{t}"
        for v in self.grafo.vertices.values():
            if v.nombre.lower() == t.lower():
                return v.id
        raise ValueError(f"No existe el usuario '{t}'.")

    def ficha_topologia(self):
        g = self.grafo
        n_arcos = sum(len(l) for l in g.adyacencia.values())
        grados = [(v.nombre, g.GradoEntrada(i), g.GradoSalida(i)) for i, v in g.vertices.items()]
        return {"vertices": len(g.vertices), "arcos": n_arcos, "dirigido": g.dirigido,
                "ponderado": True, "grados": grados}

    def _cargar_juegos_ejemplo(self):
        ejemplos = [("Consola", "Shooter", "First Person Shooter", "Halo"),
                    ("Consola", "Shooter", "Third Person Shooter", "Gears of War"),
                    ("Consola", "Plataforma", "Metroidvania", "Metroid"),
                    ("Consola", "Plataforma", "2D", "Mario"),
                    ("PC", "Shooter", "First Person Shooter", "Valorant"),
                    ("PC", "Shooter", "Third Person Shooter", "Deadlock"),
                    ("PC", "Plataforma", "Metroidvania", "Silksong"),
                    ("PC", "Plataforma", "2D", "Super Meat Boy")]
        for e in ejemplos:
            self.arbol_bin.insertar_juego(*e)
        for e in ejemplos + [("Consola", "Shooter", "Hero Shooter", "Marvel Rivals"),
                             ("Móvil", "Plataforma", "2D", "Dan the Man")]:
            self.arbol_nario.insertar_juego(*e)

    # =============== CORTE 1: BST vs AVL ===============
    def subir_videos(self, n_texto):
        n = _entero(n_texto, "La cantidad", 1)
        if n > 200000:
            raise ValueError("Por favor usa 200.000 videos o menos (Colab se pone lento).")
        inicio = self.videos_subidos + 1
        for id_video in range(inicio, inicio + n):
            self.bst.insertar(id_video)
            self.avl.insertar(id_video)
        self.videos_subidos += n
        return {"desde": inicio, "hasta": inicio + n - 1, "total": self.videos_subidos}

    def alturas_y_rotaciones(self):
        return {"altura_bst": self.bst.altura(), "altura_avl": self.avl.altura(),
                "rotaciones": self.avl.contador_rotaciones, "total": self.videos_subidos}

    def comparar_busqueda(self, id_texto=""):
        if self.videos_subidos == 0:
            raise ValueError("Primero sube videos.")
        id_buscado = _entero(id_texto, "El ID") if str(id_texto).strip() else self.videos_subidos
        ok_b, pasos_b = self.bst.buscar(id_buscado)
        ok_a, pasos_a = self.avl.buscar(id_buscado)
        reps = 2000
        t0 = time.perf_counter()
        for _ in range(reps):
            self.bst.buscar(id_buscado)
        t_bst = time.perf_counter() - t0
        t0 = time.perf_counter()
        for _ in range(reps):
            self.avl.buscar(id_buscado)
        t_avl = time.perf_counter() - t0
        return {"id": id_buscado, "encontrado": ok_b and ok_a, "pasos_bst": pasos_b,
                "pasos_avl": pasos_a, "t_bst": t_bst, "t_avl": t_avl, "reps": reps,
                "log2": self.videos_subidos.bit_length() - 1}

    def reiniciar_indices_video(self):
        self.bst, self.avl, self.videos_subidos = ArbolBST(), ArbolAVL(), 0

    # =============== CORTE 1: arboles de clasificacion ===============
    def _arbol(self, tipo):
        return self.arbol_bin if tipo == "binario" else self.arbol_nario

    def juego_insertar(self, tipo, plataforma, genero, subgenero, juego):
        self._arbol(tipo).insertar_juego(plataforma, genero, subgenero, juego)

    def juego_eliminar(self, tipo, nivel, plataforma, genero, subgenero, juego):
        a = self._arbol(tipo)
        if nivel == "Juego":
            ok = a.eliminar_juego(plataforma, genero, subgenero, juego)
        elif nivel == "Subgénero":
            ok = a.eliminar_subgenero(plataforma, genero, subgenero)
        else:
            ok = a.eliminar_genero(plataforma, genero)
        if not ok:
            raise ValueError("No se encontró esa ruta en el árbol.")

    def juego_recorrido(self, tipo, recorrido):
        return self._arbol(tipo).obtener_recorrido(recorrido)

    # =============== CORTE 1: Arbol B (usuarios) ===============
    def usuario_insertar(self, id_texto, nombre):
        if not nombre.strip():
            raise ValueError("El nombre no puede estar vacío.")
        self.indice_usuarios.insertar(_entero(id_texto, "El ID"), nombre.strip())

    def usuario_buscar(self, id_texto):
        return self.indice_usuarios.buscar(_entero(id_texto, "El ID"))

    def usuario_eliminar(self, id_texto):
        return self.indice_usuarios.eliminar(_entero(id_texto, "El ID"))

    def usuarios_inorden(self):
        return self.indice_usuarios.inorden()

    def usuarios_niveles(self):
        return self.indice_usuarios.por_niveles()

    # =============== CORTE 1: Arbol B+ (tags) ===============
    def tag_indexar(self, tag, video):
        if not tag.strip() or not video.strip():
            raise ValueError("Escribe el tag y el ID del video.")
        self.indice_tags.indexar_video(tag.strip(), video.strip())

    def tag_buscar(self, tag):
        return self.indice_tags.buscar_videos_por_tag(tag.strip())

    def tag_desde(self, tag):
        return self.indice_tags.listar_tags_desde(tag.strip())

    def tag_quitar(self, tag, video):
        return self.indice_tags.quitar_video_de_tag(tag.strip(), video.strip())

    def tags_recorrido(self, tipo):
        return self.indice_tags.obtener_recorrido(tipo)

    # =============== CORTE 1: Trie ===============
    def recargar_catalogo(self):
        self.catalogo = datos.leer_catalogo()
        self.trie = Trie()
        for _, nombre, pop in self.catalogo:
            self.trie.insertar(nombre, pop)
        return len(self.catalogo)

    def trie_autocompletar(self, prefijo, k_texto="5"):
        k = _entero(k_texto, "K", 1) if str(k_texto).strip() else 5
        return self.trie.autocompletar_top_k(prefijo.strip(), k)

    def trie_memoria(self):
        nombres = [n for _, n, _ in self.catalogo]
        b_trie = memoria_trie_en_bytes(self.trie)
        b_lista = memoria_lista_en_bytes(nombres)
        b_set = memoria_set_en_bytes(nombres)
        return {"titulos": len(nombres), "trie": b_trie, "lista": b_lista, "set": b_set,
                "nodos": self.trie.contar_nodos(),
                "trie_gana": b_trie < min(b_lista, b_set)}

    # =============== CORTE 1: Heap ===============
    def recargar_reportes(self):
        self.cola = MaxHeap()
        reportes = datos.leer_reportes()
        self.cola.construir_heap(reportes)
        return len(reportes)

    def cola_estado(self):
        return [(r.id_reporte, r.gravedad, r.descripcion) for r in self.cola.pendientes_ordenados()]

    def cola_insertar(self, id_reporte, gravedad, descripcion):
        if not id_reporte.strip():
            raise ValueError("Escribe el ID del reporte.")
        self.cola.insertar(Reporte(id_reporte.strip(), _entero(gravedad, "La gravedad", 0),
                                   descripcion.strip()))

    def cola_cambiar(self, id_reporte, gravedad):
        if not self.cola.cambiar_prioridad(id_reporte.strip(), _entero(gravedad, "La gravedad", 0)):
            raise ValueError("No se encontró ese reporte (¿ya fue atendido?).")

    def cola_envejecer(self, incremento):
        n = _entero(incremento, "El incremento", 1)
        self.cola.envejecer_todos(n)
        return len(self.cola.arreglo)

    def cola_atender(self):
        r = self.cola.extraer_max()
        if r is None:
            raise ValueError("No hay reportes pendientes.")
        return (r.id_reporte, r.gravedad, r.descripcion)

    def cola_guardar_orden(self):
        """Atiende TODO en orden sobre una copia y lo guarda en Excel (no vacia la cola real)."""
        copia = MaxHeap()
        copia.construir_heap([Reporte(r.id_reporte, r.gravedad, r.descripcion)
                              for r in self.cola.arreglo])
        filas, pos = [], 1
        while not copia.esta_vacio():
            r = copia.extraer_max()
            filas.append({"orden_atencion": pos, "id_reporte": r.id_reporte,
                          "gravedad": r.gravedad, "descripcion": r.descripcion})
            pos += 1
        return datos.guardar_orden_atencion(filas), len(filas)

    # =============== CORTE 2: Grafo ===============
    def usuarios_grafo(self):
        return [(v.nombre, v.id) for v in self.grafo.vertices.values()]

    def posiciones(self):
        """Posicion (x, y) de cada usuario para dibujar el grafo."""
        return {i: (v.datos.get("x", 0), v.datos.get("y", 0)) for i, v in self.grafo.vertices.items()}

    def nombre(self, id_v):
        return self.grafo.vertices[id_v].nombre

    def relaciones(self):
        g = self.grafo
        return [(g.vertices[a].nombre, g.vertices[b].nombre, p, g.capacidad.get((a, b)))
                for a, lista in g.adyacencia.items() for b, p in lista]

    def recorrido(self, tipo, inicio):
        g = self.grafo
        if tipo == "BFS":
            return [g.vertices[i].nombre for i in g.RecorridoAnchura(inicio)]
        return [v.nombre for v in g.RecorridoProfundidad(inicio)]

    def dijkstra(self, origen):
        D, P = self.grafo.Dijkstra(origen)
        filas = []
        for v in self.grafo.vertices:
            if D[v] == float("inf"):
                filas.append((self.nombre(v), "inalcanzable", "—"))
            else:
                ruta = " → ".join(self.nombre(i) for i in reconstruir_camino(P, v))
                filas.append((self.nombre(v), D[v], ruta))
        return filas

    def floyd(self, con_promocion=False):
        g = self.grafo_promo if con_promocion else self.grafo
        ids, D, _, _ = g.FloydWarshall()
        return [g.vertices[i].nombre for i in ids], D

    # ---- Parcial: retos ----
    def reto1(self, origen, destino):
        ruta, cuello = self.grafo.RutaMayorCapacidad(origen, destino)
        return [self.nombre(i) for i in ruta], cuello

    def reto2(self, referencia):
        return [(v.nombre, [self.nombre(i) for i in perdidos])
                for v, perdidos in self.grafo.DetectarPuntosCriticosDeFalla(referencia)]

    def reto3(self, origen, destino):
        r = self.grafo.GenerarRutaConRespaldo(origen, destino)
        for k in ("ruta_primaria", "ruta_respaldo"):
            if k in r:
                r[k] = [self.nombre(i) for i in r[k]]
        return r

    def reto4(self):
        ids, D, _, _ = self.grafo_promo.FloydWarshall()
        nombres = [self.grafo_promo.vertices[i].nombre for i in ids]
        diagonal = [(nombres[i], D[i][i]) for i in range(len(ids))]
        anomalias = detectar_anomalia_ciclo_negativo(D, nombres)
        return {"diagonal": diagonal, "anomalias": anomalias,
                "acciones": ACCIONES_CICLO_NEGATIVO if anomalias else []}

    # ---- CORTE 3: Welsh-Powell (el grafo de conflictos se arma solo desde los eventos) ----
    def welsh_powell(self, descendente=True):
        if not self.eventos:
            raise ValueError("No hay eventos cargados.")
        grafo = col.construir_grafo_conflictos(self.eventos)
        grados = col.calcular_grados(grafo)
        orden = col.ordenar_por_grado(grados, descendente)
        color = col.welsh_powell(grafo, orden)
        nombres = {i: v.nombre for i, v in self.grafo.vertices.items()}
        descripcion = {e: f"{ev['nombre']} ({', '.join(nombres.get(u, u) for u in ev['participantes'])})"
                       for e, ev in self.eventos.items()}
        motivos = [(a, b, col.motivo_conflicto(self.eventos, a, b, nombres))
                   for a in grafo for b in grafo[a] if a < b]
        n = max(color.values())
        return {"grados": grados, "orden": orden, "turnos": col.agrupar_por_turno(color),
                "valida": col.es_coloracion_valida(grafo, color), "n_turnos": n,
                "eventos": descripcion, "conflictos": grafo, "motivos": motivos,
                "negocio": (f"Se requieren {n} franjas horarias mínimas para que ningún streamer "
                            f"ni servidor quede en dos eventos al mismo tiempo.")}

    # ---- CORTE 3: Busqueda BFS / DFS / UCS ----
    def comparar_busquedas(self, inicio, meta):
        ady = self.grafo.adyacencia
        salida = {}
        for nombre, f in bus.ALGORITMOS.items():
            r = f(ady, inicio, meta)
            r["camino_nombres"] = [self.nombre(i) for i in r["camino"]] if r["camino"] else None
            salida[nombre] = r
        return salida

    # ---- Modulo 2: consultas operativas ----
    def bfs_sugerencias(self, inicio, max_nivel=3):
        inicio = self.resolver_usuario(inicio)
        niveles = bus.bfs_niveles(self.grafo.adyacencia, inicio, max_nivel)
        return {"inicio": self.nombre(inicio),
                "niveles": {k: [self.nombre(i) for i in v] for k, v in niveles.items()},
                "sugerencias": [self.nombre(i) for i in niveles.get(2, [])]}

    def ciclos_dfs(self):
        ciclos = bus.detectar_ciclos_dfs(self.grafo.adyacencia)
        return [[self.nombre(i) for i in c] for c in ciclos]

    def ruta_ucs(self, inicio, meta):
        inicio, meta = self.resolver_usuario(inicio), self.resolver_usuario(meta)
        if inicio == meta:
            raise ValueError("El inicio y la meta son el mismo usuario.")
        r = bus.ucs(self.grafo.adyacencia, inicio, meta)
        r["camino_nombres"] = [self.nombre(i) for i in r["camino"]] if r["camino"] else None
        r["inicio"], r["meta"] = self.nombre(inicio), self.nombre(meta)
        return r

    # ---- CORTE 3: TSP (ruta de reparto de premios) ----
    def tsp_premios(self, ganadores=None):
        ganadores = ganadores or self.red.get("ganadores_fest", [])
        ganadores = [self.resolver_usuario(g) for g in ganadores]
        if not ganadores:
            raise ValueError("Elige al menos un ganador.")
        b = self.red["bodega"]
        puntos = [("BODEGA", b["lat"], b["lon"])]
        for g in dict.fromkeys(ganadores):
            datos_u = self.grafo.vertices[g].datos
            puntos.append((g, datos_u["lat"], datos_u["lon"]))
        d = tsp_mod.matriz_distancias(puntos)
        ids = [p[0] for p in puntos]
        aprox = tsp_mod.tsp_aproximado_mst(ids, d)
        try:
            exacto = tsp_mod.tsp_exacto(ids, d)
        except ValueError:
            exacto = None
        nom = lambda i: b["nombre"] if i == "BODEGA" else self.nombre(i)
        loc = lambda i: b["localidad"] if i == "BODEGA" else self.grafo.vertices[i].datos.get("localidad", "")
        tramos = [(nom(x), nom(y), d[(x, y)]) for x, y in zip(aprox["ruta"], aprox["ruta"][1:])]
        return {"puntos": {i: (nom(i), loc(i), la, lo) for i, la, lo in puntos},
                "aprox": aprox, "exacto": exacto, "tramos": tramos,
                "ruta_aprox_nombres": [nom(i) for i in aprox["ruta"]],
                "ruta_exacta_nombres": [nom(i) for i in exacto["ruta"]] if exacto else None,
                "razon": (aprox["costo"] / exacto["costo"]) if exacto and exacto["costo"] else None,
                "cota": round(2 * aprox["peso_mst"], 2)}

    # ---- Evidencia de ejecucion (registro JSON) ----
    def exportar_evidencia(self, ruta=None):
        import datetime
        b = self.comparar_busquedas("U1", "U4")
        wp = self.welsh_powell()
        t = self.tsp_premios()
        vc_r = self.vertex_cover()
        registro = {
            "proyecto": "Gamefolks", "fecha": datetime.datetime.now().isoformat(timespec="seconds"),
            "red": {k: v for k, v in self.ficha_topologia().items() if k != "grados"},
            "modulo2_busqueda": {
                "consulta": "Ruta de invitación de Juana_Gamer (U1) a AndresPlay (U4)",
                **{alg: {"camino": r["camino_nombres"], "saltos": r["saltos"], "costo": r["costo"],
                         "expandidos": r["expandidos"]} for alg, r in b.items()},
                "bfs_niveles_desde_U1": self.bfs_sugerencias("U1")["niveles"],
                "ciclos_dfs": self.ciclos_dfs(),
            },
            "modulo3_welsh_powell": {"turnos": wp["turnos"], "numero_cromatico_aprox": wp["n_turnos"],
                                     "valida": wp["valida"], "negocio": wp["negocio"]},
            "tsp_premios": {"ruta_aproximada": t["ruta_aprox_nombres"], "km_aproximada": t["aprox"]["costo"],
                            "ruta_optima": t["ruta_exacta_nombres"],
                            "km_optima": t["exacto"]["costo"] if t["exacto"] else None},
            "vertex_cover": {"aproximacion": sorted(vc_r["nombres"][x] for x in vc_r["aprox"]),
                             "optimo": sorted(vc_r["nombres"][x] for x in vc_r["optimo"])},
        }
        return datos.guardar_evidencia(registro, ruta) if ruta else datos.guardar_evidencia(registro)

    # ---- CORTE 3: Vertex Cover ----
    def vertex_cover(self):
        aristas = vc.aristas_sin_direccion(self.grafo)
        aprox, elegidas = vc.cobertura_aproximada(aristas)
        voraz = vc.cobertura_voraz_por_grado(aristas)
        optimo = vc.cobertura_optima(aristas)
        n = self.nombre
        return {
            "aristas": aristas,
            "elegidas": [(n(u), n(v)) for u, v in elegidas],
            "aprox": aprox, "voraz": voraz, "optimo": optimo,
            "nombres": {i: nombre for nombre, i in self.usuarios_grafo()},
            "validas": {"aprox": vc.es_cobertura(aristas, aprox),
                        "voraz": vc.es_cobertura(aristas, voraz),
                        "optimo": vc.es_cobertura(aristas, optimo)},
            "razon": len(aprox) / len(optimo),
        }
