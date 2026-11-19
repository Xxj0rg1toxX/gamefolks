"""
MODELO - Welsh-Powell (coloracion voraz de grafos) para programar eventos en vivo.
Color = turno (franja horaria). Tomado de welsh_powell_gamefolks.py.
"""

EVENTOS = {
    "E1": "Torneo Valorant (Valentina_Streams)",
    "E2": "Speedrun Marathon (DiegoSpeedrun, CamilaRPG)",
    "E3": "Charla RPG (CamilaRPG, Valentina_Streams)",
    "E4": "Taller de Builds (NicoBuilds, AndresPlay)",
    "E5": "Torneo Cooperativo (Juana_Gamer, Camilo92)",
    "E6": "Maraton Retro (DiegoSpeedrun, LauraFPS)",
    "E7": "Q&A Comunidad (Valentina_Streams, Juana_Gamer)",
    "E8": "Subasta de Skins (AndresPlay, SofiaGG)",
}

# Conflicto = comparten streamer/moderador o servidor en la misma franja (grafo NO dirigido)
GRAFO_CONFLICTOS = {
    "E1": ["E3", "E7"],
    "E2": ["E3", "E6"],
    "E3": ["E1", "E2", "E7"],
    "E4": ["E5", "E8"],
    "E5": ["E4", "E7"],
    "E6": ["E2"],
    "E7": ["E1", "E3", "E5"],
    "E8": ["E4"],
}


def calcular_grados(grafo):
    return {v: len(vec) for v, vec in grafo.items()}


def ordenar_por_grado(grados, descendente=True):
    """sorted es estable: en empate se respeta el orden E1, E2, ..."""
    return sorted(grados, key=lambda v: grados[v], reverse=descendente)


def welsh_powell(grafo, orden):
    color, turno = {}, 0
    while len(color) < len(grafo):
        turno += 1
        for v in orden:
            if v in color:
                continue
            if all(color.get(u) != turno for u in grafo[v]):
                color[v] = turno
    return color


def agrupar_por_turno(color):
    turnos = {}
    for v, t in color.items():
        turnos.setdefault(t, []).append(v)
    return {t: sorted(vs, key=lambda x: int(x[1:])) for t, vs in sorted(turnos.items())}


def es_coloracion_valida(grafo, color):
    return all(color[v] != color[u] for v in grafo for u in grafo[v])


def construir_grafo_conflictos(eventos):
    """eventos = {id: {"participantes": [...], "servidor": "S-..."}}.
    Dos eventos chocan (arista) si comparten un participante o el mismo servidor.
    Devuelve la lista de adyacencia NO dirigida {evento: [eventos en conflicto]}."""
    ids = list(eventos)
    grafo = {e: [] for e in ids}
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            comparten = set(eventos[a]["participantes"]) & set(eventos[b]["participantes"])
            mismo_servidor = eventos[a].get("servidor") and eventos[a].get("servidor") == eventos[b].get("servidor")
            if comparten or mismo_servidor:
                grafo[a].append(b)
                grafo[b].append(a)
    return grafo


def motivo_conflicto(eventos, a, b, nombres=None):
    nombres = nombres or {}
    comunes = sorted(set(eventos[a]["participantes"]) & set(eventos[b]["participantes"]))
    partes = [f"comparten a {', '.join(nombres.get(u, u) for u in comunes)}"] if comunes else []
    if eventos[a].get("servidor") and eventos[a].get("servidor") == eventos[b].get("servidor"):
        partes.append(f"mismo servidor {eventos[a]['servidor']}")
    return " y ".join(partes)
