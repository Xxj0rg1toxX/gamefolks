"""
WEB - Almacén de datos en memoria (reemplaza a SQLite en la versión GitHub Pages).
Guarda las mismas tablas que la versión Flask (usuarios, seguimientos, publicaciones,
likes, comentarios, eventos, participantes, reportes) como listas y diccionarios de Python.
Se puede exportar a JSON para que el navegador lo guarde en localStorage.
Los algoritmos NO usan este almacén: servicios.py lo lee y arma las estructuras
propias del modelo (Grafo, Trie, MaxHeap...).
"""
import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timedelta

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_RED = os.path.join(RAIZ, "data", "red_gamefolks.json")
CLAVE_DEMO = "gamefolks123"


def hash_clave(clave, sal=None):
    """Hash con sal (sha256). Es una demo local: los datos viven solo en el navegador."""
    sal = sal or secrets.token_hex(8)
    return f"{sal}${hashlib.sha256((sal + clave).encode('utf-8')).hexdigest()}"


def clave_correcta(clave, guardado):
    sal = guardado.split("$", 1)[0]
    return hmac.compare_digest(hash_clave(clave, sal), guardado)


def _hace(horas):
    return (datetime.now() - timedelta(hours=horas)).isoformat(timespec="seconds")


def numero(id_):
    """'U12' -> 12 (para ordenar ids como en la base original)."""
    return int(id_[1:])


PUBLICACIONES_DEMO = [
    ("U3", "¡Hoy en vivo a las 7 pm! Rankeds de Valorant con la comunidad 🎮", "Valorant", 1),
    ("U8", "Terminé la granja automática de hierro. Tutorial completo en mi perfil.", "Minecraft", 2),
    ("U1", "¿Alguien para un cooperativo el domingo? Necesitamos un controlador.", "Valorant", 3),
    ("U10", "Nuevo récord personal en Celeste Capítulo 1: 1:58.3 ⏱️", "Celeste", 4),
    ("U9", "Mi paladín por fin llegó al acto 3 sin perder a nadie del grupo.", "Baldur's Gate 3", 5),
    ("U4", "Abrí 30 sobres y no me salió ni un jugador decente. Así no se puede.", "EA FC 25", 6),
    ("U5", "Tip de support: el ward en el río salva más partidas que cualquier kill.", "League of Legends", 8),
    ("U7", "AWP o nada. ¿Qué mapa juegan más ustedes?", "Counter-Strike 2", 10),
    ("U2", "Construí la Torre Colpatria en Minecraft a escala 1:1 (casi).", "Minecraft", 12),
    ("U6", "Victoria magistral número 100 🏆", "Fortnite", 14),
    ("U6", "¡¡Ganen skins gratis entrando a este link!! 🔗🔗🔗", "Fortnite", 16),
    ("U4", "El que no juega en mi equipo es un manco, mejor desinstalen.", "EA FC 25", 18),
]
COMENTARIOS_DEMO = [(1, "U1", "¡Allá estaré!"), (1, "U2", "Guárdame un puesto en la ranked"),
                    (2, "U2", "Lo voy a copiar ya mismo"), (4, "U9", "Qué locura de tiempo"),
                    (5, "U10", "El acto 3 es lo mejor")]
LIKES_DEMO = [(1, "U1"), (1, "U2"), (1, "U4"), (1, "U5"), (2, "U2"), (2, "U3"), (3, "U3"), (4, "U9"),
              (5, "U10"), (7, "U3"), (9, "U8"), (10, "U3")]
REPORTES_DEMO = [(11, "U3", "Spam o estafa", 60, 2), (12, "U3", "Acoso o bullying", 80, 0),
                 (12, "U8", "Acoso o bullying", 80, 1), (6, "U5", "Otro", 30, 3)]

TABLAS = ("usuarios", "seguimientos", "publicaciones", "likes", "comentarios",
          "eventos", "participantes", "reportes", "contadores")


class Almacen:
    def __init__(self):
        self.usuarios = {}          # id -> dict
        self.seguimientos = []      # [{origen, destino, peso, capacidad}] en orden de inserción
        self.publicaciones = []     # [{id, autor, texto, juego, creado}]
        self.likes = []             # [[publicacion, usuario]]
        self.comentarios = []       # [{id, publicacion, autor, texto, creado}]
        self.eventos = {}           # id -> {id, nombre, juego, servidor, creador}
        self.participantes = []     # [[evento, usuario]]
        self.reportes = []          # [{id, publicacion, reportero, motivo, gravedad, estado, creado}]
        self.contadores = {"publicacion": 0, "comentario": 0, "reporte": 0}

    # ------------------------------------------------ siembra y persistencia
    def sembrar(self):
        with open(RUTA_RED, encoding="utf-8") as f:
            red = json.load(f)
        clave = hash_clave(CLAVE_DEMO)
        for u in red["usuarios"]:
            self.usuarios[u["id"]] = {
                "id": u["id"], "usuario": u["usuario"], "clave_hash": clave, "bio": u["bio"], "juego": u["juego"],
                "localidad": u["localidad"], "lat": u["lat"], "lon": u["lon"], "x": u["x"], "y": u["y"],
                "rol": "moderador" if u["id"] == "U1" else "usuario", "creado": _hace(24 * 30)}
        for r in red["relaciones"]:
            self.seguimientos.append({"origen": r["origen"], "destino": r["destino"],
                                      "peso": r["peso"], "capacidad": r["capacidad"]})
        for e in red["eventos"]:
            self.eventos[e["id"]] = {"id": e["id"], "nombre": e["nombre"], "juego": e["juego"],
                                     "servidor": e["servidor"], "creador": e["participantes"][0]}
            for p in e["participantes"]:
                self.participantes.append([e["id"], p])
        for autor, texto, juego, horas in PUBLICACIONES_DEMO:
            self.nueva_publicacion(autor, texto, juego, _hace(horas))
        for pub, autor, texto in COMENTARIOS_DEMO:
            self.nuevo_comentario(pub, autor, texto, _hace(1))
        for pub, u in LIKES_DEMO:
            self.likes.append([pub, u])
        for pub, quien, motivo, grav, dias in REPORTES_DEMO:
            self.nuevo_reporte(pub, quien, motivo, grav, _hace(24 * dias))
        return self

    def exportar(self):
        return {t: getattr(self, t) for t in TABLAS}

    @classmethod
    def importar(cls, datos):
        a = cls()
        for t in TABLAS:
            if t not in datos:
                raise ValueError("Los datos guardados están incompletos.")
            setattr(a, t, datos[t])
        return a

    # ------------------------------------------------ usuarios
    def usuarios_ordenados(self):
        return sorted(self.usuarios.values(), key=lambda u: numero(u["id"]))

    def usuario_por_nombre(self, nombre):
        """El nombre de usuario no distingue mayúsculas (igual que COLLATE NOCASE)."""
        nombre = (nombre or "").lower()
        return next((u for u in self.usuarios.values() if u["usuario"].lower() == nombre), None)

    def siguiente_id_usuario(self):
        return f"U{max((numero(i) for i in self.usuarios), default=0) + 1}"

    # ------------------------------------------------ seguimientos
    def seguimiento(self, origen, destino):
        return next((s for s in self.seguimientos if s["origen"] == origen and s["destino"] == destino), None)

    # ------------------------------------------------ publicaciones, comentarios, reportes
    def nueva_publicacion(self, autor, texto, juego, creado):
        self.contadores["publicacion"] += 1
        p = {"id": self.contadores["publicacion"], "autor": autor, "texto": texto, "juego": juego, "creado": creado}
        self.publicaciones.append(p)
        return p

    def publicacion(self, pid):
        return next((p for p in self.publicaciones if p["id"] == pid), None)

    def nuevo_comentario(self, publicacion, autor, texto, creado):
        self.contadores["comentario"] += 1
        c = {"id": self.contadores["comentario"], "publicacion": publicacion, "autor": autor,
             "texto": texto, "creado": creado}
        self.comentarios.append(c)
        return c

    def nuevo_reporte(self, publicacion, reportero, motivo, gravedad, creado):
        self.contadores["reporte"] += 1
        r = {"id": self.contadores["reporte"], "publicacion": publicacion, "reportero": reportero,
             "motivo": motivo, "gravedad": gravedad, "estado": "pendiente", "creado": creado}
        self.reportes.append(r)
        return r

    def borrar_publicacion(self, pid):
        self.likes = [l for l in self.likes if l[0] != pid]
        self.comentarios = [c for c in self.comentarios if c["publicacion"] != pid]
        self.publicaciones = [p for p in self.publicaciones if p["id"] != pid]

    # ------------------------------------------------ eventos
    def eventos_ordenados(self):
        return sorted(self.eventos.values(), key=lambda e: numero(e["id"]))

    def siguiente_id_evento(self):
        return f"E{max((numero(i) for i in self.eventos), default=0) + 1}"
