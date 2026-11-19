"""
MODELO - Arbol B (indice de usuarios por ID) y Arbol B+ (indice de videos por tag).
Portado de ArbolB_IndiceUsuarios.java y ArbolBMas_IndiceTags.java.
Orden 4: maximo 3 claves y 4 hijos por nodo.
"""

MAX_CLAVES = 3


# ===================================================================
# ARBOL B
# ===================================================================
class NodoB:
    def __init__(self, es_hoja):
        self.claves = []
        self.datos = []
        self.hijos = []
        self.es_hoja = es_hoja


class ArbolB:
    def __init__(self):
        self.raiz = NodoB(True)

    def insertar(self, clave, dato):
        if self.buscar(clave) is not None:
            raise ValueError(f"Ya existe la clave {clave}.")
        if len(self.raiz.claves) == MAX_CLAVES:
            nueva = NodoB(False)
            nueva.hijos.append(self.raiz)
            self._dividir_hijo(nueva, 0)
            self.raiz = nueva
        self._insertar_no_lleno(self.raiz, clave, dato)

    def _dividir_hijo(self, padre, i):
        hijo = padre.hijos[i]
        medio = len(hijo.claves) // 2
        clave_media, dato_medio = hijo.claves[medio], hijo.datos[medio]
        nuevo = NodoB(hijo.es_hoja)
        nuevo.claves = hijo.claves[medio + 1:]
        nuevo.datos = hijo.datos[medio + 1:]
        if not hijo.es_hoja:
            nuevo.hijos = hijo.hijos[medio + 1:]
            hijo.hijos = hijo.hijos[:medio + 1]
        hijo.claves = hijo.claves[:medio]
        hijo.datos = hijo.datos[:medio]
        padre.claves.insert(i, clave_media)
        padre.datos.insert(i, dato_medio)
        padre.hijos.insert(i + 1, nuevo)

    def _insertar_no_lleno(self, nodo, clave, dato):
        i = len(nodo.claves) - 1
        while i >= 0 and clave < nodo.claves[i]:
            i -= 1
        if nodo.es_hoja:
            nodo.claves.insert(i + 1, clave)
            nodo.datos.insert(i + 1, dato)
        else:
            i += 1
            if len(nodo.hijos[i].claves) == MAX_CLAVES:
                self._dividir_hijo(nodo, i)
                if clave > nodo.claves[i]:
                    i += 1
            self._insertar_no_lleno(nodo.hijos[i], clave, dato)

    def buscar(self, clave):
        nodo = self.raiz
        while True:
            i = 0
            while i < len(nodo.claves) and clave > nodo.claves[i]:
                i += 1
            if i < len(nodo.claves) and nodo.claves[i] == clave:
                return nodo.datos[i]
            if nodo.es_hoja:
                return None
            nodo = nodo.hijos[i]

    def eliminar(self, clave):
        """Caso simple (igual que en el taller): solo claves en hojas.
        Devuelve (exito, mensaje)."""
        nodo = self.raiz
        while True:
            if clave in nodo.claves:
                if nodo.es_hoja:
                    idx = nodo.claves.index(clave)
                    del nodo.claves[idx]
                    del nodo.datos[idx]
                    return True, "Eliminado."
                return False, ("La clave está en un nodo interno; eliminarla ahí requiere "
                               "el caso avanzado (no cubierto en el taller).")
            if nodo.es_hoja:
                return False, "No existe esa clave."
            i = 0
            while i < len(nodo.claves) and clave > nodo.claves[i]:
                i += 1
            nodo = nodo.hijos[i]

    def inorden(self):
        lista = []

        def visitar(n):
            for i, c in enumerate(n.claves):
                if not n.es_hoja:
                    visitar(n.hijos[i])
                lista.append((c, n.datos[i]))
            if not n.es_hoja:
                visitar(n.hijos[len(n.claves)])
        visitar(self.raiz)
        return lista

    def por_niveles(self):
        """Lista de niveles; cada nivel es una lista de nodos (lista de claves)."""
        niveles, actual = [], [self.raiz]
        while actual:
            niveles.append([list(n.claves) for n in actual])
            actual = [h for n in actual for h in n.hijos]
        return niveles

    def altura(self):
        return len(self.por_niveles())


# ===================================================================
# ARBOL B+
# ===================================================================
class NodoBMas:
    def __init__(self, es_hoja):
        self.claves = []
        self.hijos = []
        self.videos_por_tag = []     # solo hojas
        self.es_hoja = es_hoja
        self.siguiente = None        # solo hojas: enlace a la proxima hoja


class ArbolBMas:
    def __init__(self):
        self.raiz = NodoBMas(True)

    def indexar_video(self, tag, id_video):
        if len(self.raiz.claves) == MAX_CLAVES:
            nueva = NodoBMas(False)
            nueva.hijos.append(self.raiz)
            self._dividir_hijo(nueva, 0)
            self.raiz = nueva
        self._insertar_no_lleno(self.raiz, tag, id_video)

    def _dividir_hijo(self, padre, i):
        hijo = padre.hijos[i]
        medio = len(hijo.claves) // 2
        nuevo = NodoBMas(hijo.es_hoja)
        if hijo.es_hoja:
            separador = hijo.claves[medio]                 # se COPIA al padre
            nuevo.claves = hijo.claves[medio:]
            nuevo.videos_por_tag = hijo.videos_por_tag[medio:]
            hijo.claves = hijo.claves[:medio]
            hijo.videos_por_tag = hijo.videos_por_tag[:medio]
            nuevo.siguiente = hijo.siguiente
            hijo.siguiente = nuevo
            padre.claves.insert(i, separador)
        else:
            clave_media = hijo.claves[medio]               # SUBE (se quita de abajo)
            nuevo.claves = hijo.claves[medio + 1:]
            nuevo.hijos = hijo.hijos[medio + 1:]
            hijo.hijos = hijo.hijos[:medio + 1]
            hijo.claves = hijo.claves[:medio]
            padre.claves.insert(i, clave_media)
        padre.hijos.insert(i + 1, nuevo)

    def _insertar_no_lleno(self, nodo, tag, id_video):
        if nodo.es_hoja:
            if tag in nodo.claves:
                nodo.videos_por_tag[nodo.claves.index(tag)].append(id_video)
                return
            i = len(nodo.claves) - 1
            while i >= 0 and tag < nodo.claves[i]:
                i -= 1
            nodo.claves.insert(i + 1, tag)
            nodo.videos_por_tag.insert(i + 1, [id_video])
        else:
            i = len(nodo.claves) - 1
            while i >= 0 and tag < nodo.claves[i]:
                i -= 1
            i += 1
            if len(nodo.hijos[i].claves) == MAX_CLAVES:
                self._dividir_hijo(nodo, i)
                if tag >= nodo.claves[i]:
                    i += 1
            self._insertar_no_lleno(nodo.hijos[i], tag, id_video)

    def _encontrar_hoja(self, tag):
        nodo = self.raiz
        while not nodo.es_hoja:
            i = 0
            while i < len(nodo.claves) and tag >= nodo.claves[i]:
                i += 1
            nodo = nodo.hijos[i]
        return nodo

    def buscar_videos_por_tag(self, tag):
        hoja = self._encontrar_hoja(tag)
        if tag not in hoja.claves:
            return []
        return list(hoja.videos_por_tag[hoja.claves.index(tag)])

    def listar_tags_desde(self, tag_inicio):
        """Recorrido secuencial por el enlace 'siguiente' entre hojas."""
        resultado = []
        hoja = self._encontrar_hoja(tag_inicio)
        i = 0
        while i < len(hoja.claves) and hoja.claves[i] < tag_inicio:
            i += 1
        while hoja is not None:
            while i < len(hoja.claves):
                resultado.append((hoja.claves[i], list(hoja.videos_por_tag[i])))
                i += 1
            hoja, i = hoja.siguiente, 0
        return resultado

    def quitar_video_de_tag(self, tag, id_video):
        hoja = self._encontrar_hoja(tag)
        if tag not in hoja.claves:
            return False
        lista = hoja.videos_por_tag[hoja.claves.index(tag)]
        if id_video in lista:
            lista.remove(id_video)
            return True
        return False

    def preorden(self):
        lista = []

        def visitar(n, prof):
            sangria = "  " * prof
            if n.es_hoja:
                for c, v in zip(n.claves, n.videos_por_tag):
                    lista.append(f"{sangria}{c} -> {v}")
            else:
                lista.append(f"{sangria}separadores: {n.claves}")
                for h in n.hijos:
                    visitar(h, prof + 1)
        visitar(self.raiz, 0)
        return lista

    def por_niveles(self):
        resultado, cola, i = [], [self.raiz], 0
        while i < len(cola):
            n = cola[i]
            i += 1
            resultado.append(("Hoja " if n.es_hoja else "Interno ") + str(n.claves))
            cola.extend(n.hijos)
        return resultado

    def obtener_recorrido(self, tipo):
        return self.por_niveles() if tipo == "niveles" else self.preorden()
