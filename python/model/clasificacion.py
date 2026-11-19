"""
MODELO - Arboles de clasificacion de videojuegos.
Portado de ArbolBinarioJuegos.java y ArbolClasificacionJuegos.java.
Ruta: Plataforma -> Genero -> Subgenero -> Juego.
"""


class NodoJuego:
    def __init__(self, dato, nivel):
        self.dato = dato
        self.nivel = nivel
        self.hijos = []          # binario: max 2 ; N-ario: sin limite


class _ArbolClasificacion:
    MAX_HIJOS = None             # None = sin limite

    def __init__(self):
        self.raiz = NodoJuego("Contenido", "Raíz")

    # ---------- insercion jerarquica ----------
    def insertar_juego(self, plataforma, genero, subgenero, juego):
        """Lanza ValueError si un nodo binario ya tiene 2 hijos distintos."""
        for campo, valor in (("plataforma", plataforma), ("género", genero),
                             ("subgénero", subgenero), ("juego", juego)):
            if not valor or not valor.strip():
                raise ValueError(f"El campo {campo} no puede estar vacío.")
        n1 = self._obtener_o_crear(self.raiz, plataforma.strip(), "Plataforma")
        n2 = self._obtener_o_crear(n1, genero.strip(), "Género")
        n3 = self._obtener_o_crear(n2, subgenero.strip(), "Subgénero")
        self._obtener_o_crear(n3, juego.strip(), "Juego")

    def _obtener_o_crear(self, padre, nombre, nivel):
        for h in padre.hijos:
            if h.dato.lower() == nombre.lower():
                return h
        if self.MAX_HIJOS is not None and len(padre.hijos) >= self.MAX_HIJOS:
            raise ValueError(f"No se pudo insertar '{nombre}': '{padre.dato}' "
                             f"ya tiene {self.MAX_HIJOS} hijos (árbol binario).")
        nuevo = NodoJuego(nombre, nivel)
        padre.hijos.append(nuevo)
        return nuevo

    # ---------- busqueda / eliminacion ----------
    def _hijo(self, padre, nombre):
        if padre is None:
            return None
        for h in padre.hijos:
            if h.dato.lower() == nombre.lower():
                return h
        return None

    def _ruta(self, *nombres):
        nodo = self.raiz
        for nombre in nombres:
            nodo = self._hijo(nodo, nombre)
            if nodo is None:
                return None
        return nodo

    def _eliminar_hijo(self, padre, nombre):
        if padre is None:
            return False
        for i, h in enumerate(padre.hijos):
            if h.dato.lower() == nombre.lower():
                del padre.hijos[i]       # se va el nodo y todo lo que cuelga
                return True
        return False

    def eliminar_juego(self, plataforma, genero, subgenero, juego):        # caso hoja
        return self._eliminar_hijo(self._ruta(plataforma, genero, subgenero), juego)

    def eliminar_subgenero(self, plataforma, genero, subgenero):           # caso 1+ hijos
        return self._eliminar_hijo(self._ruta(plataforma, genero), subgenero)

    def eliminar_genero(self, plataforma, genero):                         # caso 2 hijos
        return self._eliminar_hijo(self._ruta(plataforma), genero)

    # ---------- recorridos ----------
    def preorden(self):
        lista = []

        def visitar(nodo, prof):
            lista.append(("  " * prof) + f"{nodo.dato} ({nodo.nivel})")
            for h in nodo.hijos:
                visitar(h, prof + 1)
        visitar(self.raiz, 0)
        return lista

    def por_niveles(self):
        resultado, cola, i = [], [self.raiz], 0
        while i < len(cola):
            nodo = cola[i]
            i += 1
            resultado.append(f"{nodo.dato} ({nodo.nivel})")
            cola.extend(nodo.hijos)
        return resultado

    def obtener_recorrido(self, tipo):
        return self.por_niveles() if tipo == "niveles" else self.preorden()

    def contar_juegos(self):
        total, pila = 0, [self.raiz]
        while pila:
            n = pila.pop()
            if n.nivel == "Juego":
                total += 1
            pila.extend(n.hijos)
        return total


class ArbolBinarioJuegos(_ArbolClasificacion):
    """Arbol BINARIO: maximo 2 hijos por nodo."""
    MAX_HIJOS = 2


class ArbolNarioJuegos(_ArbolClasificacion):
    """Arbol N-ario: cualquier cantidad de hijos."""
    MAX_HIJOS = None
