"""Prueba la API de la app web con el cliente de pruebas de Flask (sin abrir el navegador)."""
import os, sys, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "python"))


class Respuesta:
    def __init__(self, texto):
        d = json.loads(texto)
        self.status_code, self.json = d["estado"], d["cuerpo"]


class Cliente:
    """Imita el cliente de pruebas de Flask, pero contra el despachador local."""
    def __init__(self, app):
        self.app = app

    def _pedir(self, metodo, url, json_=None):
        return Respuesta(self.app.manejar(metodo, url, json.dumps(json_) if json_ is not None else ""))

    def get(self, url): return self._pedir("GET", url)
    def post(self, url, json=None): return self._pedir("POST", url, json)
    def put(self, url, json=None): return self._pedir("PUT", url, json)
    def delete(self, url): return self._pedir("DELETE", url)

from web.api import Aplicacion

c = Cliente(Aplicacion())
assert c.get("/api/feed").status_code == 401                         # sin sesion
assert c.post("/api/login", json={"usuario": "Juana_Gamer", "clave": "mala"}).status_code == 400
assert c.post("/api/login", json={"usuario": "juana_gamer", "clave": "gamefolks123"}).json["rol"] == "moderador"
assert any(s["usuario"] == "NicoBuilds" and s["nivel"] == 2 for s in c.get("/api/explorar").json["sugerencias"])  # BFS
r = c.get("/api/ruta?hasta=U4").json
assert r["UCS"]["costo"] == 17 and r["BFS"]["costo"] == 20                                     # UCS vs BFS
assert c.get("/api/ruta?hasta=U9").json["UCS"]["camino"] is None                              # inalcanzable
assert c.get("/api/ciclos").json["total"] == 4                                                # DFS
assert c.get("/api/buscar?q=va").json["usuarios"][0]["usuario"] == "Valentina_Streams"       # Trie
e = c.get("/api/eventos").json
assert e["n_turnos"] == 3 and e["valida"]                                                     # Welsh-Powell
p = c.post("/api/premios", json={"ganadores": ["U1", "U3", "U4", "U5", "U7", "U9", "U10"]}).json
assert p["exacto"]["km"] <= p["aprox"]["km"] <= 2 * p["exacto"]["km"]                         # TSP
m = c.get("/api/moderacion").json
assert [x["prioridad"] for x in m["cola"]] == sorted((x["prioridad"] for x in m["cola"]), reverse=True)  # Heap
assert len(m["monitorear"]["aprox"]) <= 2 * len(m["monitorear"]["optimo"])                    # Vertex Cover
assert c.post("/api/moderacion/atender", json={"accion": "descartar"}).json["atendido"]["prioridad"] == m["cola"][0]["prioridad"]
assert c.post("/api/publicaciones", json={"texto": "  "}).status_code == 400
pid = c.post("/api/publicaciones", json={"texto": "hola", "juego": "Halo"}).json["id"]
assert c.post(f"/api/publicaciones/{pid}/like").json["me_gusta"] is True
assert c.post(f"/api/publicaciones/{pid}/reportar", json={"motivo": "No existe"}).status_code == 400
assert c.post("/api/eventos", json={"nombre": "X", "servidor": "S-LATAM-2", "participantes": ["U3"]}).status_code == 201
assert c.post("/api/usuarios/U1/seguir").status_code == 400                                  # seguirse a si mismo
# laboratorio: todos los talleres
assert len(c.get("/api/lab/usuarios").json) == 10
acciones = {"avl_subir": {"n": "500"}, "avl_buscar": {}, "juegos_ver": {"tipo": "nario"}, "b_ver": {}, "b_insertar": {"id": "1099", "nombre": "Profe"},
            "bmas_ver": {}, "bmas_desde": {"tag": "A"}, "trie_top": {"prefijo": "ha"}, "trie_memoria": {}, "heap_ver": {}, "heap_atender": {},
            "grafo_ficha": {}, "grafo_recorrido": {"tipo": "DFS", "inicio": "U1"}, "dijkstra": {"origen": "U1"}, "floyd": {"promocion": "si"},
            "reto1": {"origen": "U1", "destino": "U3"}, "reto2": {"referencia": "U1"}, "reto3": {"origen": "U1", "destino": "U8"}, "reto4": {},
            "busqueda_comparar": {"origen": "U1", "destino": "U4"}, "bfs_niveles": {"origen": "U1"}, "dfs_ciclos": {},
            "welsh_powell": {"orden": "mayor"}, "vertex_cover": {}, "tsp": {}, "reiniciar_todo": {}}
for a, datos in acciones.items():
    r = c.post(f"/api/lab/{a}", json=datos)
    assert r.status_code == 200 and r.json["bloques"], a
assert "25" in str(c.post("/api/lab/reto1", json={"origen": "U1", "destino": "U3"}).json)                 # cuello de botella del C2
assert c.post("/api/lab/trie_top", json={"prefijo": "h"}).status_code == 400                               # prefijo corto
assert c.post("/api/lab/no_existe", json={}).status_code == 400
c.post("/api/logout")
assert c.post("/api/registro", json={"usuario": "nuevo_1", "clave": "123456", "localidad": "Suba"}).status_code == 201
assert c.get("/api/moderacion").status_code == 403                                           # no es moderador
assert c.post("/api/registro", json={"usuario": "nuevo_1", "clave": "123456", "localidad": "Suba"}).status_code == 400
# persistencia: exportar -> importar conserva usuarios, posts y sesion
c2 = Cliente(Aplicacion(c.app.exportar()))
assert c2.get("/api/yo").json["usuario"] == "nuevo_1"
assert any(u["usuario"] == "nuevo_1" for u in c2.get("/api/usuarios").json)
assert Aplicacion("basura").manejar("GET", "/api/catalogos")                                  # datos corruptos -> reinicia
print("API LOCAL OK")
