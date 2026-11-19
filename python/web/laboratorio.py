"""
WEB - Laboratorio: todos los talleres del semestre dentro de la app.
Usa el MISMO Controlador del parcial (controller/controlador.py) sobre la red
original de los talleres (data/red_gamefolks.json), para que los resultados
coincidan con los documentos. Cada usuario tiene su propio laboratorio en memoria.

Cada accion devuelve una lista de "bloques" que el frontend sabe pintar:
  {"tipo": "ok"/"aviso", "texto"}            mensajes
  {"tipo": "tabla", "titulo", "columnas", "filas"}
  {"tipo": "texto", "titulo", "lineas"}      arboles en preorden, etc.
  {"tipo": "red", "titulo", "nodos", "aristas", "camino", "camino2"}
"""
from controller.controlador import Controlador

_labs = {}
ACCIONES = {}


def laboratorio_de(uid):
    if uid not in _labs:
        _labs[uid] = Controlador()
    return _labs[uid]


def reiniciar(uid):
    _labs[uid] = Controlador()


def usuarios(uid):
    return [{"id": i, "usuario": v.nombre} for i, v in laboratorio_de(uid).grafo.vertices.items()]


def accion(nombre):
    def registrar(f):
        ACCIONES[nombre] = f
        return f
    return registrar


def ejecutar(uid, nombre, datos):
    if nombre == "reiniciar_todo":
        reiniciar(uid)
        return [ok("Laboratorio reiniciado con los datos originales de los talleres.")]
    if nombre not in ACCIONES:
        raise ValueError("Acción de laboratorio desconocida.")
    return ACCIONES[nombre](laboratorio_de(uid), {k: str(v) for k, v in (datos or {}).items()})


# ---------------- bloques ----------------
def ok(texto):
    return {"tipo": "ok", "texto": texto}


def aviso(texto):
    return {"tipo": "aviso", "texto": texto}


def tabla(titulo, columnas, filas):
    return {"tipo": "tabla", "titulo": titulo, "columnas": columnas, "filas": [[str(x) for x in f] for f in filas]}


def texto(titulo, lineas):
    return {"tipo": "texto", "titulo": titulo, "lineas": [str(l) for l in lineas]}


def red(c, titulo, camino=(), camino2=(), grafo=None):
    g = grafo or c.grafo
    nodos = [{"id": i, "usuario": v.nombre, "x": v.datos.get("x", 0), "y": v.datos.get("y", 0)} for i, v in g.vertices.items()]
    aristas = [{"a": a, "b": b, "peso": p} for a, lista in g.adyacencia.items() for b, p in lista]
    return {"tipo": "red", "titulo": titulo, "nodos": nodos, "aristas": aristas,
            "camino": list(camino or []), "camino2": list(camino2 or [])}


def flecha(nombres):
    return " → ".join(nombres) if nombres else "sin solución"


# =====================================================================
# CORTE 1
# =====================================================================
@accion("avl_subir")
def avl_subir(c, d):
    r = c.subir_videos(d.get("n", "1000"))
    a = c.alturas_y_rotaciones()
    return [ok(f"Se subieron los videos {r['desde']} a {r['hasta']} (total {r['total']}). Los IDs llegan en orden: el peor caso del BST."),
            tabla("Altura de cada índice", ["Índice", "Altura", "Comentario"],
                  [["BST", a["altura_bst"], "se volvió una lista"], ["AVL", a["altura_avl"], f"{a['rotaciones']} rotaciones para mantenerse balanceado"]])]


@accion("avl_buscar")
def avl_buscar(c, d):
    r = c.comparar_busqueda(d.get("id", ""))
    return [tabla(f"Buscar el video {r['id']}", ["Árbol", "Comparaciones", f"Tiempo de {r['reps']} búsquedas"],
                  [["BST", r["pasos_bst"], f"{r['t_bst']:.4f} s"], ["AVL", r["pasos_avl"], f"{r['t_avl']:.4f} s"]]),
            ok(f"log2(n) ≈ {r['log2']}: así se ve el O(log n) del AVL frente al O(n) del BST desbalanceado.")]


@accion("avl_reiniciar")
def avl_reiniciar(c, d):
    c.reiniciar_indices_video()
    return [ok("Índices de videos vacíos.")]


def _ruta_juego(d):
    return d.get("tipo", "binario"), d.get("plataforma", ""), d.get("genero", ""), d.get("subgenero", ""), d.get("juego", "")


@accion("juegos_insertar")
def juegos_insertar(c, d):
    tipo, *ruta = _ruta_juego(d)
    c.juego_insertar(tipo, *ruta)
    return [ok(f"'{ruta[3]}' insertado en el árbol {tipo}."), texto("PreOrden", c.juego_recorrido(tipo, "preorden"))]


@accion("juegos_eliminar")
def juegos_eliminar(c, d):
    tipo, *ruta = _ruta_juego(d)
    c.juego_eliminar(tipo, d.get("nivel", "Juego"), *ruta)
    return [ok("Eliminado junto con todo lo que colgaba de ese nodo."), texto("PreOrden", c.juego_recorrido(tipo, "preorden"))]


@accion("juegos_ver")
def juegos_ver(c, d):
    tipo = d.get("tipo", "binario")
    return [texto(f"Árbol {tipo} · PreOrden (reporte jerárquico)", c.juego_recorrido(tipo, "preorden")),
            texto("Por niveles (cola)", c.juego_recorrido(tipo, "niveles"))]


def _arbol_b(c):
    return [tabla("Árbol B de orden 4 por niveles", ["Nivel", "Nodos (claves)"],
                  [[i, "   ".join(str(n) for n in nodos)] for i, nodos in enumerate(c.usuarios_niveles())]),
            tabla("Directorio en orden (InOrden)", ["ID", "Nombre"], c.usuarios_inorden())]


@accion("b_insertar")
def b_insertar(c, d):
    c.usuario_insertar(d.get("id", ""), d.get("nombre", ""))
    return [ok("Usuario insertado.")] + _arbol_b(c)


@accion("b_buscar")
def b_buscar(c, d):
    r = c.usuario_buscar(d.get("id", ""))
    return [ok(f"ID {d.get('id')} → {r}") if r else aviso(f"No existe el ID {d.get('id')}.")]


@accion("b_eliminar")
def b_eliminar(c, d):
    hecho, msg = c.usuario_eliminar(d.get("id", ""))
    return [ok(msg) if hecho else aviso(msg)] + _arbol_b(c)


@accion("b_ver")
def b_ver(c, d):
    return _arbol_b(c)


@accion("bmas_indexar")
def bmas_indexar(c, d):
    c.tag_indexar(d.get("tag", ""), d.get("video", ""))
    return [ok(f"Video {d.get('video')} indexado bajo '{d.get('tag')}'."), texto("Estructura por niveles", c.tags_recorrido("niveles"))]


@accion("bmas_buscar")
def bmas_buscar(c, d):
    r = c.tag_buscar(d.get("tag", ""))
    return [ok(f"'{d.get('tag')}' → {', '.join(r)}") if r else aviso(f"No hay videos con el tag '{d.get('tag')}'.")]


@accion("bmas_desde")
def bmas_desde(c, d):
    return [tabla("Recorrido secuencial por las hojas enlazadas", ["Tag", "Videos"],
                  [[t, ", ".join(v)] for t, v in c.tag_desde(d.get("tag", ""))])]


@accion("bmas_quitar")
def bmas_quitar(c, d):
    hecho = c.tag_quitar(d.get("tag", ""), d.get("video", ""))
    return [ok("Video quitado del tag.") if hecho else aviso("Ese video no estaba en ese tag.")]


@accion("bmas_ver")
def bmas_ver(c, d):
    return [texto("PreOrden (separadores y hojas)", c.tags_recorrido("preorden")),
            texto("Por niveles", c.tags_recorrido("niveles"))]


@accion("trie_top")
def trie_top(c, d):
    r = c.trie_autocompletar(d.get("prefijo", ""), d.get("k", "5"))
    if not r:
        return [aviso("Sin coincidencias.")]
    return [tabla(f"Top-{len(r)} para '{d.get('prefijo')}'", ["#", "Título", "Vistas"],
                  [[i, n, f"{p:,}".replace(",", ".")] for i, (n, p) in enumerate(r, 1)])]


@accion("trie_memoria")
def trie_memoria(c, d):
    m = c.trie_memoria()
    return [tabla(f"Memoria con {m['titulos']} títulos", ["Estructura", "Bytes"],
                  [["Trie", f"{m['trie']:,} ({m['nodos']} nodos)".replace(",", ".")], ["Lista", f"{m['lista']:,}".replace(",", ".")],
                   ["Set", f"{m['set']:,}".replace(",", ".")]]),
            ok("El Trie es el más liviano." if m["trie_gana"] else
               "Con pocos títulos el Trie pesa más que una lista en Python (cada nodo es un objeto); gana cuando hay muchos prefijos compartidos.")]


def _heap(c, titulo="Cola de moderación"):
    arreglo = c.cola.arreglo
    filas = [[i, r.id_reporte, r.gravedad, (i - 1) // 2 if i else "—", r.descripcion] for i, r in enumerate(arreglo[:15])]
    return [tabla(f"{titulo}: arreglo interno del Max-Heap (primeras 15 posiciones)",
                  ["Posición", "ID", "Gravedad", "Padre", "Descripción"], filas),
            ok(f"{len(arreglo)} reportes pendientes · heap válido (cada padre ≥ sus hijos): {c.cola.es_heap_valido()}")]


@accion("heap_ver")
def heap_ver(c, d):
    return _heap(c)


@accion("heap_insertar")
def heap_insertar(c, d):
    c.cola_insertar(d.get("id", ""), d.get("gravedad", ""), d.get("descripcion", ""))
    return [ok(f"Reporte {d.get('id')} insertado (sube con 'burbujear').")] + _heap(c)


@accion("heap_cambiar")
def heap_cambiar(c, d):
    c.cola_cambiar(d.get("id", ""), d.get("gravedad", ""))
    return [ok(f"Gravedad de {d.get('id')} cambiada a {d.get('gravedad')} (changePriority en O(log n)).")] + _heap(c)


@accion("heap_envejecer")
def heap_envejecer(c, d):
    n = c.cola_envejecer(d.get("incremento", "5"))
    return [ok(f"Se sumaron {d.get('incremento')} puntos a {n} reportes (envejecimiento contra la inanición).")] + _heap(c)


@accion("heap_atender")
def heap_atender(c, d):
    i, g, desc = c.cola_atender()
    return [ok(f"Atendido el más urgente: [{i}] gravedad {g} — {desc}")] + _heap(c)


@accion("heap_recargar")
def heap_recargar(c, d):
    n = c.recargar_reportes()
    return [ok(f"Cola recargada con {n} reportes.")] + _heap(c)


# =====================================================================
# CORTE 2
# =====================================================================
@accion("grafo_ficha")
def grafo_ficha(c, d):
    f = c.ficha_topologia()
    return [ok(f"Grafo {'dirigido' if f['dirigido'] else 'no dirigido'} y ponderado · |V| = {f['vertices']} usuarios · |E| = {f['arcos']} relaciones 'sigue a'."),
            red(c, "Red de los talleres (peso sobre cada flecha)"),
            tabla("Grados", ["Usuario", "Lo siguen (entrada)", "Sigue a (salida)"], f["grados"]),
            tabla("Lista de adyacencia", ["Usuario", "Sigue a (vecino, peso)"],
                  [[v.nombre, ", ".join(f"{c.nombre(b)} ({p})" for b, p in c.grafo.adyacencia[i])] for i, v in c.grafo.vertices.items()])]


@accion("grafo_recorrido")
def grafo_recorrido(c, d):
    tipo = d.get("tipo", "BFS")
    inicio = c.resolver_usuario(d.get("inicio", "U1"))
    orden = c.recorrido(tipo, inicio)
    return [tabla(f"Recorrido {tipo} desde {c.nombre(inicio)}", ["Orden de visita"], [[flecha(orden)]]),
            ok("BFS usa una cola (por niveles); DFS una pila/recursión (se va a fondo por el primer vecino).")]


@accion("dijkstra")
def dijkstra(c, d):
    origen = c.resolver_usuario(d.get("origen", "U1"))
    return [tabla(f"Dijkstra desde {c.nombre(origen)}", ["Destino", "Costo mínimo", "Ruta"], c.dijkstra(origen))]


@accion("floyd")
def floyd(c, d):
    promo = d.get("promocion", "no") == "si"
    nombres, D = c.floyd(promo)
    filas = [[nombres[i]] + ["∞" if x == float("inf") else x for x in D[i]] for i in range(len(nombres))]
    corto = [n.split("_")[0][:9] for n in nombres]
    return [tabla("Floyd-Warshall: distancias mínimas entre todos los pares" + (" (con la promoción U3 → U1 = −30)" if promo else ""),
                  [""] + corto, filas)]


@accion("reto1")
def reto1(c, d):
    a, b = c.resolver_usuario(d.get("origen", "U1")), c.resolver_usuario(d.get("destino", "U3"))
    ruta, cuello = c.reto1(a, b)
    if not ruta:
        return [aviso("No existe ninguna ruta entre esos usuarios.")]
    ids = [c.resolver_usuario(n) for n in ruta]
    return [tabla("Reto 1: ruta de mayor capacidad (cuello de botella máximo)", ["Ruta", "Cuello de botella"], [[flecha(ruta), cuello]]),
            red(c, "Ruta de mayor capacidad", ids)]


@accion("reto2")
def reto2(c, d):
    ref = c.resolver_usuario(d.get("referencia", "U1"))
    crit = c.reto2(ref)
    if not crit:
        return [ok("No hay puntos críticos: la red es resiliente desde ese usuario.")]
    return [tabla(f"Reto 2: puntos críticos de falla (referencia {c.nombre(ref)})", ["Si se cae…", "Quedan desconectados"],
                  [[n, ", ".join(p)] for n, p in crit])]


@accion("reto3")
def reto3(c, d):
    a, b = c.resolver_usuario(d.get("origen", "U1")), c.resolver_usuario(d.get("destino", "U8"))
    r = c.reto3(a, b)
    bloques = []
    if "ruta_respaldo" in r:
        bloques.append(tabla("Reto 3: ruta primaria y de respaldo (sin arcos en común)", ["Tipo", "Ruta", "Costo"],
                             [["Primaria", flecha(r["ruta_primaria"]), r["costo_primaria"]],
                              ["Respaldo", flecha(r["ruta_respaldo"]), r["costo_respaldo"]]]))
        bloques.append(ok(f"El respaldo cuesta {r['diferencia_pct']:+.1f} % frente a la primaria."))
        bloques.append(red(c, "Rosa = primaria · azul = respaldo", [c.resolver_usuario(n) for n in r["ruta_primaria"]],
                           [c.resolver_usuario(n) for n in r["ruta_respaldo"]]))
    else:
        bloques.append(aviso(r.get("alerta", "Sin resultado.")))
        if "ruta_primaria" in r:
            bloques.append(tabla("Ruta primaria (única)", ["Ruta", "Costo"], [[flecha(r["ruta_primaria"]), r["costo_primaria"]]]))
    return bloques


@accion("reto4")
def reto4(c, d):
    r = c.reto4()
    bloques = [tabla("Reto 4: diagonal de Floyd-Warshall con la promoción U3 → U1 = −30", ["Usuario", "D[i][i]"], r["diagonal"])]
    for nodo, val in r["anomalias"]:
        bloques.append(aviso(f"ALERTA DE ARBITRAJE: ciclo de peso negativo en {nodo} (D[i][i] = {val} < 0)"))
    if r["acciones"]:
        bloques.append(texto("Acciones a tomar", [f"- {a}" for a in r["acciones"]]))
    return bloques


# =====================================================================
# CORTE 3
# =====================================================================
@accion("busqueda_comparar")
def busqueda_comparar(c, d):
    a, b = c.resolver_usuario(d.get("origen", "U1")), c.resolver_usuario(d.get("destino", "U4"))
    r = c.comparar_busquedas(a, b)
    bloques = [tabla(f"{c.nombre(a)} → {c.nombre(b)}", ["Algoritmo", "Camino", "Saltos", "Costo", "Expandidos", "Generados", "Frontera máx."],
                     [[k, flecha(x["camino_nombres"]), x["saltos"], x["costo"], " ".join(x["expandidos"]), x["generados"], x["frontera_max"]]
                      for k, x in r.items()])]
    if r["UCS"]["camino"]:
        bloques.append(red(c, "Rosa = UCS (menor costo) · azul = BFS (menos saltos)", r["UCS"]["camino"], r["BFS"]["camino"]))
    else:
        bloques.append(aviso("La meta es inalcanzable desde ese inicio."))
    return bloques


@accion("bfs_niveles")
def bfs_niveles(c, d):
    r = c.bfs_sugerencias(d.get("origen", "U1"))
    return [tabla(f"BFS por niveles desde {r['inicio']}", ["Nivel", "Usuarios"], [[k, ", ".join(v)] for k, v in r["niveles"].items()]),
            ok("Sugerencias (nivel 2): " + (", ".join(r["sugerencias"]) or "ninguna"))]


@accion("dfs_ciclos")
def dfs_ciclos(c, d):
    cs = c.ciclos_dfs()
    return [tabla("DFS: ciclos encontrados (arcos de retroceso)", ["#", "Ciclo"], [[i, flecha(x)] for i, x in enumerate(cs, 1)])]


@accion("welsh_powell")
def welsh_powell(c, d):
    desc = d.get("orden", "mayor") != "menor"
    r = c.welsh_powell(desc)
    return [tabla("Grafo de conflictos", ["Evento", "Descripción", "Grado"], [[e, r["eventos"][e], r["grados"][e]] for e in r["conflictos"]]),
            tabla("¿Por qué chocan?", ["Eventos", "Motivo"], [[f"{a} – {b}", m] for a, b, m in r["motivos"]]),
            ok("Orden: " + " > ".join(f"{e}({r['grados'][e]})" for e in r["orden"])),
            tabla("Asignación de turnos", ["Turno", "Eventos"], [[f"Turno {k}", ", ".join(v)] for k, v in r["turnos"].items()]),
            ok(f"Número cromático obtenido: {r['n_turnos']} · sin colisiones: {r['valida']}. {r['negocio']}")]


@accion("vertex_cover")
def vertex_cover(c, d):
    r = c.vertex_cover()
    n = r["nombres"]
    filas = [[t, len(r[k]), ", ".join(sorted(n[x] for x in r[k])), r["validas"][k]]
             for t, k in (("2-aproximación", "aprox"), ("Voraz por grado", "voraz"), ("Óptimo (fuerza bruta)", "optimo"))]
    return [tabla(f"{len(r['aristas'])} interacciones", ["Método", "Usuarios", "Monitoreados", "Cubre todo"], filas),
            ok("Interacciones elegidas por la 2-aproximación: " + "; ".join(f"{a} – {b}" for a, b in r["elegidas"])),
            ok(f"Aproximación / óptimo = {r['razon']:.2f} (la garantía dice ≤ 2).")]


@accion("tsp")
def tsp(c, d):
    texto_g = d.get("ganadores", "").strip()
    ganadores = [x for x in texto_g.split(",") if x.strip()] if texto_g else None
    r = c.tsp_premios(ganadores)
    bloques = [tabla("Ruta aproximada (árbol mínimo + preorden)", ["#", "Desde", "Hasta", "km"],
                     [[i, a, b, km] for i, (a, b, km) in enumerate(r["tramos"], 1)])]
    filas = [["Aproximación MST", flecha(r["ruta_aprox_nombres"]), r["aprox"]["costo"]]]
    if r["exacto"]:
        filas.append(["Óptimo (fuerza bruta)", flecha(r["ruta_exacta_nombres"]), r["exacto"]["costo"]])
    bloques.append(tabla("Comparación", ["Método", "Ruta", "km"], filas))
    if r["exacto"]:
        bloques.append(ok(f"Aproximación / óptimo = {r['razon']:.2f} · árbol mínimo = {r['aprox']['peso_mst']} km · "
                          f"{r['exacto']['rutas_probadas']} rutas probadas por la fuerza bruta."))
    return bloques
