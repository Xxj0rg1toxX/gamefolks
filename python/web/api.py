"""
WEB - API de Gamefolks para GitHub Pages.
Las mismas rutas /api/... de la versión Flask, pero como un despachador en Python puro que
corre DENTRO del navegador (Pyodide). El frontend sigue usando fetch(); puente.js intercepta
las llamadas a /api/ y las pasa a manejar().
"""
import json
import re
from datetime import datetime
from urllib.parse import parse_qs, urlsplit

from . import laboratorio as lab, servicios as srv
from .almacen import Almacen, clave_correcta, hash_clave


class ErrorHttp(Exception):
    def __init__(self, estado, mensaje):
        super().__init__(mensaje)
        self.estado, self.mensaje = estado, mensaje


class Aplicacion:
    def __init__(self, datos_guardados=None):
        self.uid = None
        self.con = None
        if datos_guardados:
            try:
                guardado = json.loads(datos_guardados)
                self.con = Almacen.importar(guardado["datos"])
                self.uid = guardado.get("uid")
            except (ValueError, KeyError, TypeError):
                self.con = None
        if self.con is None:
            self.reiniciar()
        self.rutas = []
        self._registrar_rutas()

    # ------------------------------------------------ persistencia
    def reiniciar(self):
        self.con = Almacen().sembrar()
        self.uid = None
        lab._labs.clear()

    def exportar(self):
        return json.dumps({"datos": self.con.exportar(), "uid": self.uid}, ensure_ascii=False)

    # ------------------------------------------------ entrada
    def manejar(self, metodo, url, cuerpo_json=""):
        """-> JSON string {"estado": int, "cuerpo": ...}"""
        try:
            cuerpo = json.loads(cuerpo_json) if cuerpo_json else {}
            if not isinstance(cuerpo, dict):
                cuerpo = {}
        except ValueError:
            cuerpo = {}
        partes = urlsplit(url)
        consulta = {k: v[0] for k, v in parse_qs(partes.query).items()}
        try:
            for m, patron, funcion in self.rutas:
                if m != metodo:
                    continue
                encaje = patron.fullmatch(partes.path)
                if encaje:
                    estado, datos = funcion(cuerpo, consulta, **encaje.groupdict())
                    return json.dumps({"estado": estado, "cuerpo": datos}, ensure_ascii=False)
            raise ErrorHttp(404, "No encontrado.")
        except ErrorHttp as e:
            return json.dumps({"estado": e.estado, "cuerpo": {"error": e.mensaje}}, ensure_ascii=False)
        except ValueError as e:
            return json.dumps({"estado": 400, "cuerpo": {"error": str(e)}}, ensure_ascii=False)
        except Exception as e:                      # nunca se cae: responde 500 con el mensaje
            return json.dumps({"estado": 500, "cuerpo": {"error": f"Error interno: {e}"}}, ensure_ascii=False)

    # ------------------------------------------------ utilidades
    @staticmethod
    def ahora():
        return datetime.now().isoformat(timespec="seconds")

    def login_requerido(self):
        if not self.uid or self.uid not in self.con.usuarios:
            self.uid = None
            raise ErrorHttp(401, "Inicia sesión para continuar.")
        return self.uid

    def moderador_requerido(self):
        yo = self.login_requerido()
        if self.con.usuarios[yo]["rol"] != "moderador":
            raise ErrorHttp(403, "Solo los moderadores pueden ver esto.")
        return yo

    def perfil_publico(self, uid):
        c = self.con
        u = c.usuarios.get(uid)
        if not u:
            raise ValueError("Ese usuario no existe.")
        datos = {k: u[k] for k in ("id", "usuario", "bio", "juego", "localidad", "rol")}
        datos["seguidores"] = sum(1 for s in c.seguimientos if s["destino"] == uid)
        datos["siguiendo"] = sum(1 for s in c.seguimientos if s["origen"] == uid)
        datos["publicaciones"] = sum(1 for p in c.publicaciones if p["autor"] == uid)
        if self.uid:
            datos["lo_sigo"] = c.seguimiento(self.uid, uid) is not None
            datos["me_sigue"] = c.seguimiento(uid, self.uid) is not None
        return datos

    def publicaciones(self, filtro):
        c = self.con
        filas = []
        for p in c.publicaciones:
            if not filtro(p):
                continue
            filas.append({**p, "autor_nombre": c.usuarios[p["autor"]]["usuario"],
                          "autor_juego": c.usuarios[p["autor"]]["juego"],
                          "n_likes": sum(1 for l in c.likes if l[0] == p["id"]),
                          "n_comentarios": sum(1 for m in c.comentarios if m["publicacion"] == p["id"]),
                          "me_gusta": [p["id"], self.uid] in c.likes, "mia": p["autor"] == self.uid})
        filas.sort(key=lambda f: (f["creado"], f["id"]), reverse=True)
        return filas[:60]

    def _sumar_interaccion(self, pid, puntos):
        """Cada like o comentario suma al peso (interacciones/semana) del arco 'yo -> autor'."""
        p = self.con.publicacion(pid)
        if not p:
            raise ValueError("Esa publicación ya no existe.")
        s = self.con.seguimiento(self.uid, p["autor"])
        if s:
            s["peso"] += puntos

    def _comentarios(self, pid):
        c = self.con
        return [{**m, "autor_nombre": c.usuarios[m["autor"]]["usuario"]}
                for m in sorted((m for m in c.comentarios if m["publicacion"] == pid), key=lambda m: m["id"])]

    # ------------------------------------------------ rutas
    def _registrar_rutas(self):
        def ruta(metodo, patron):
            def deco(f):
                self.rutas.append((metodo, re.compile(patron), f))
                return f
            return deco

        # ---- sesión
        @ruta("POST", "/api/registro")
        def registro(d, q):
            usuario = (d.get("usuario") or "").strip()
            clave = d.get("clave") or ""
            localidad = d.get("localidad") or ""
            if not (3 <= len(usuario) <= 20) or not all(ch.isalnum() or ch == "_" for ch in usuario):
                raise ValueError("El usuario debe tener de 3 a 20 letras, números o guion bajo.")
            if len(clave) < 6:
                raise ValueError("La contraseña debe tener al menos 6 caracteres.")
            if localidad not in srv.LOCALIDADES:
                raise ValueError("Elige tu localidad (la usamos para enviarte premios).")
            if self.con.usuario_por_nombre(usuario):
                raise ValueError("Ese nombre de usuario ya está ocupado.")
            uid = self.con.siguiente_id_usuario()
            lat, lon = srv.LOCALIDADES[localidad]
            self.con.usuarios[uid] = {
                "id": uid, "usuario": usuario, "clave_hash": hash_clave(clave), "bio": (d.get("bio") or "")[:160],
                "juego": (d.get("juego") or "")[:40], "localidad": localidad, "lat": lat, "lon": lon,
                "x": None, "y": None, "rol": "usuario", "creado": self.ahora()}
            self.uid = uid
            return 201, self.perfil_publico(uid)

        @ruta("POST", "/api/login")
        def login(d, q):
            u = self.con.usuario_por_nombre((d.get("usuario") or "").strip())
            if not u or not clave_correcta(d.get("clave") or "", u["clave_hash"]):
                raise ValueError("Usuario o contraseña incorrectos.")
            self.uid = u["id"]
            return 200, self.perfil_publico(u["id"])

        @ruta("POST", "/api/logout")
        def logout(d, q):
            self.uid = None
            return 200, {"ok": True}

        @ruta("GET", "/api/yo")
        def mi_perfil(d, q):
            return 200, self.perfil_publico(self.login_requerido())

        @ruta("PUT", "/api/yo")
        def editar_perfil(d, q):
            yo = self.login_requerido()
            localidad = d.get("localidad")
            if localidad not in srv.LOCALIDADES:
                raise ValueError("Elige una localidad de la lista.")
            lat, lon = srv.LOCALIDADES[localidad]
            self.con.usuarios[yo].update(bio=(d.get("bio") or "")[:160], juego=(d.get("juego") or "")[:40],
                                         localidad=localidad, lat=lat, lon=lon)
            return 200, self.perfil_publico(yo)

        @ruta("GET", "/api/catalogos")
        def catalogos(d, q):
            return 200, {"localidades": list(srv.LOCALIDADES), "servidores": srv.SERVIDORES,
                         "motivos": list(srv.MOTIVOS)}

        # ---- publicaciones
        @ruta("GET", "/api/feed")
        def feed(d, q):
            yo = self.login_requerido()
            sigo = {s["destino"] for s in self.con.seguimientos if s["origen"] == yo}
            return 200, self.publicaciones(lambda p: p["autor"] == yo or p["autor"] in sigo)

        @ruta("GET", "/api/descubrir")
        def descubrir(d, q):
            self.login_requerido()
            return 200, self.publicaciones(lambda p: True)

        @ruta("POST", "/api/publicaciones")
        def publicar(d, q):
            yo = self.login_requerido()
            texto = (d.get("texto") or "").strip()
            if not texto:
                raise ValueError("Escribe algo antes de publicar.")
            if len(texto) > 400:
                raise ValueError("Máximo 400 caracteres.")
            p = self.con.nueva_publicacion(yo, texto, (d.get("juego") or "").strip()[:40], self.ahora())
            return 201, self.publicaciones(lambda x: x["id"] == p["id"])[0]

        @ruta("DELETE", r"/api/publicaciones/(?P<pid>\d+)")
        def borrar(d, q, pid):
            yo = self.login_requerido()
            pid = int(pid)
            p = self.con.publicacion(pid)
            if not p:
                raise ValueError("Esa publicación ya no existe.")
            if p["autor"] != yo and self.con.usuarios[yo]["rol"] != "moderador":
                raise ErrorHttp(403, "Solo puedes borrar tus publicaciones.")
            self.con.borrar_publicacion(pid)
            for r in self.con.reportes:
                if r["publicacion"] == pid:
                    r["estado"] = "atendido"
            return 200, {"ok": True}

        @ruta("POST", r"/api/publicaciones/(?P<pid>\d+)/like")
        def like(d, q, pid):
            yo = self.login_requerido()
            pid = int(pid)
            self._sumar_interaccion(pid, 0)
            par = [pid, yo]
            if par in self.con.likes:
                self.con.likes.remove(par)
                me_gusta = False
            else:
                self.con.likes.append(par)
                self._sumar_interaccion(pid, 1)
                me_gusta = True
            return 200, {"me_gusta": me_gusta, "n_likes": sum(1 for l in self.con.likes if l[0] == pid)}

        @ruta("GET", r"/api/publicaciones/(?P<pid>\d+)/comentarios")
        def ver_comentarios(d, q, pid):
            self.login_requerido()
            return 200, self._comentarios(int(pid))

        @ruta("POST", r"/api/publicaciones/(?P<pid>\d+)/comentarios")
        def comentar(d, q, pid):
            yo = self.login_requerido()
            pid = int(pid)
            texto = (d.get("texto") or "").strip()
            if not texto:
                raise ValueError("El comentario está vacío.")
            self._sumar_interaccion(pid, 2)
            self.con.nuevo_comentario(pid, yo, texto[:300], self.ahora())
            return 200, self._comentarios(pid)

        @ruta("POST", r"/api/publicaciones/(?P<pid>\d+)/reportar")
        def reportar(d, q, pid):
            yo = self.login_requerido()
            pid = int(pid)
            motivo = d.get("motivo")
            if motivo not in srv.MOTIVOS:
                raise ValueError("Elige un motivo de la lista.")
            if not self.con.publicacion(pid):
                raise ValueError("Esa publicación ya no existe.")
            if any(r["publicacion"] == pid and r["reportero"] == yo and r["estado"] == "pendiente"
                   for r in self.con.reportes):
                raise ValueError("Ya reportaste esta publicación. Los moderadores la están revisando.")
            self.con.nuevo_reporte(pid, yo, motivo, srv.MOTIVOS[motivo], self.ahora())
            return 200, {"ok": True}

        # ---- usuarios y seguir
        @ruta("GET", r"/api/usuarios/(?P<uid>[^/]+)")
        def ver_usuario(d, q, uid):
            self.login_requerido()
            return 200, {"perfil": self.perfil_publico(uid), "publicaciones": self.publicaciones(lambda p: p["autor"] == uid)}

        @ruta("POST", r"/api/usuarios/(?P<uid>[^/]+)/seguir")
        def seguir(d, q, uid):
            yo = self.login_requerido()
            if uid == yo:
                raise ValueError("No puedes seguirte a ti mismo.")
            if uid not in self.con.usuarios:
                raise ValueError("Ese usuario no existe.")
            s = self.con.seguimiento(yo, uid)
            if s:
                self.con.seguimientos.remove(s)
            else:
                self.con.seguimientos.append({"origen": yo, "destino": uid, "peso": 1, "capacidad": 10})
            return 200, self.perfil_publico(uid)

        @ruta("GET", "/api/usuarios")
        def lista_usuarios(d, q):
            self.login_requerido()
            return 200, [{k: u[k] for k in ("id", "usuario", "juego", "localidad")} for u in self.con.usuarios_ordenados()]

        # ---- algoritmos del curso
        @ruta("GET", "/api/buscar")
        def buscar(d, q):
            self.login_requerido()
            return 200, srv.buscar(self.con, q.get("q", ""))

        @ruta("GET", "/api/explorar")
        def explorar(d, q):
            yo = self.login_requerido()
            return 200, srv.sugerencias(self.con, yo) | {"juegos": srv.juegos_populares()}

        @ruta("GET", "/api/ruta")
        def ruta_ucs(d, q):
            yo = self.login_requerido()
            return 200, srv.ruta(self.con, yo, q.get("hasta", ""))

        @ruta("GET", "/api/ciclos")
        def ciclos(d, q):
            yo = self.login_requerido()
            return 200, srv.ciclos(self.con, yo)

        @ruta("GET", "/api/red")
        def red(d, q):
            self.login_requerido()
            return 200, srv.red(self.con)

        @ruta("GET", "/api/eventos")
        def eventos(d, q):
            self.login_requerido()
            return 200, srv.horario_eventos(self.con)

        @ruta("POST", "/api/eventos")
        def crear_evento(d, q):
            yo = self.login_requerido()
            srv.crear_evento(self.con, yo, d.get("nombre"), d.get("juego"), d.get("servidor"), d.get("participantes") or [])
            return 201, srv.horario_eventos(self.con)

        @ruta("POST", "/api/premios")
        def premios(d, q):
            self.login_requerido()
            return 200, srv.premios(self.con, d.get("ganadores") or [])

        @ruta("GET", "/api/moderacion")
        def moderacion(d, q):
            self.moderador_requerido()
            return 200, {"cola": srv.cola_moderacion(self.con), "monitorear": srv.monitorear(self.con)}

        @ruta("POST", "/api/moderacion/atender")
        def atender(d, q):
            self.moderador_requerido()
            hecho = srv.atender_siguiente(self.con, d.get("accion"))
            return 200, {"atendido": hecho, "cola": srv.cola_moderacion(self.con)}

        # ---- laboratorio (todos los talleres)
        @ruta("GET", "/api/lab/usuarios")
        def lab_usuarios(d, q):
            return 200, lab.usuarios(self.login_requerido())

        @ruta("POST", r"/api/lab/(?P<accion>[^/]+)")
        def lab_accion(d, q, accion):
            return 200, {"bloques": lab.ejecutar(self.login_requerido(), accion, d)}
