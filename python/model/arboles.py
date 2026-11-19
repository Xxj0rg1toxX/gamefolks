"""
MODELO - Arboles binarios de busqueda (BST y AVL).
Portado de ArbolBinario.java y reto1_bst_vs_avl.py.
Regla MVC: aqui NO hay print() ni input(); solo datos y logica.
"""


class NodoBST:
    def __init__(self, valor):
        self.valor = valor
        self.izquierdo = None
        self.derecho = None


class ArbolBST:
    def __init__(self):
        self.raiz = None
        self.cantidad = 0

    # ---------- insertar ----------
    def insertar(self, valor):
        """Devuelve True si se inserto, False si el valor ya existia."""
        if self.raiz is None:
            self.raiz = NodoBST(valor)
            self.cantidad += 1
            return True
        actual = self.raiz
        while True:
            if valor < actual.valor:
                if actual.izquierdo is None:
                    actual.izquierdo = NodoBST(valor)
                    self.cantidad += 1
                    return True
                actual = actual.izquierdo
            elif valor > actual.valor:
                if actual.derecho is None:
                    actual.derecho = NodoBST(valor)
                    self.cantidad += 1
                    return True
                actual = actual.derecho
            else:
                return False

    # ---------- eliminar (3 casos: hoja, 1 hijo, 2 hijos) ----------
    def eliminar(self, valor):
        existia = self.buscar(valor)[0]
        self.raiz = self._eliminar(self.raiz, valor)
        if existia:
            self.cantidad -= 1
        return existia

    def _eliminar(self, nodo, valor):
        if nodo is None:
            return None
        if valor < nodo.valor:
            nodo.izquierdo = self._eliminar(nodo.izquierdo, valor)
        elif valor > nodo.valor:
            nodo.derecho = self._eliminar(nodo.derecho, valor)
        else:
            if nodo.izquierdo is None:      # caso hoja o solo hijo derecho
                return nodo.derecho
            if nodo.derecho is None:        # solo hijo izquierdo
                return nodo.izquierdo
            sucesor = nodo.derecho          # 2 hijos: sucesor inorden
            while sucesor.izquierdo is not None:
                sucesor = sucesor.izquierdo
            nodo.valor = sucesor.valor
            nodo.derecho = self._eliminar(nodo.derecho, sucesor.valor)
        return nodo

    # ---------- consultas ----------
    def buscar(self, valor):
        """Devuelve (encontrado, pasos_de_comparacion)."""
        actual, pasos = self.raiz, 0
        while actual is not None:
            pasos += 1
            if valor == actual.valor:
                return True, pasos
            actual = actual.izquierdo if valor < actual.valor else actual.derecho
        return False, pasos

    def altura(self):
        if self.raiz is None:
            return 0
        mayor, pila = 0, [(self.raiz, 1)]
        while pila:
            nodo, nivel = pila.pop()
            mayor = max(mayor, nivel)
            if nodo.izquierdo:
                pila.append((nodo.izquierdo, nivel + 1))
            if nodo.derecho:
                pila.append((nodo.derecho, nivel + 1))
        return mayor

    def inorden(self):
        resultado, pila, actual = [], [], self.raiz
        while pila or actual:
            while actual:
                pila.append(actual)
                actual = actual.izquierdo
            actual = pila.pop()
            resultado.append(actual.valor)
            actual = actual.derecho
        return resultado

    def por_niveles(self):
        if self.raiz is None:
            return []
        resultado, cola, i = [], [self.raiz], 0
        while i < len(cola):
            nodo = cola[i]
            i += 1
            resultado.append(nodo.valor)
            if nodo.izquierdo:
                cola.append(nodo.izquierdo)
            if nodo.derecho:
                cola.append(nodo.derecho)
        return resultado


class NodoAVL:
    def __init__(self, valor):
        self.valor = valor
        self.izquierdo = None
        self.derecho = None
        self.altura = 1


class ArbolAVL:
    def __init__(self):
        self.raiz = None
        self.contador_rotaciones = 0
        self.cantidad = 0

    def _alt(self, n):
        return n.altura if n else 0

    def _actualizar(self, n):
        n.altura = 1 + max(self._alt(n.izquierdo), self._alt(n.derecho))

    def _balance(self, n):
        return self._alt(n.izquierdo) - self._alt(n.derecho)

    def _rotar_derecha(self, z):
        y = z.izquierdo
        z.izquierdo = y.derecho
        y.derecho = z
        self._actualizar(z)
        self._actualizar(y)
        self.contador_rotaciones += 1
        return y

    def _rotar_izquierda(self, z):
        y = z.derecho
        z.derecho = y.izquierdo
        y.izquierdo = z
        self._actualizar(z)
        self._actualizar(y)
        self.contador_rotaciones += 1
        return y

    def insertar(self, valor):
        antes = self.cantidad
        self.raiz = self._insertar(self.raiz, valor)
        return self.cantidad > antes

    def _insertar(self, nodo, valor):
        if nodo is None:
            self.cantidad += 1
            return NodoAVL(valor)
        if valor < nodo.valor:
            nodo.izquierdo = self._insertar(nodo.izquierdo, valor)
        elif valor > nodo.valor:
            nodo.derecho = self._insertar(nodo.derecho, valor)
        else:
            return nodo
        self._actualizar(nodo)
        b = self._balance(nodo)
        if b > 1 and valor < nodo.izquierdo.valor:           # Izq-Izq
            return self._rotar_derecha(nodo)
        if b < -1 and valor > nodo.derecho.valor:            # Der-Der
            return self._rotar_izquierda(nodo)
        if b > 1 and valor > nodo.izquierdo.valor:           # Izq-Der
            nodo.izquierdo = self._rotar_izquierda(nodo.izquierdo)
            return self._rotar_derecha(nodo)
        if b < -1 and valor < nodo.derecho.valor:            # Der-Izq
            nodo.derecho = self._rotar_derecha(nodo.derecho)
            return self._rotar_izquierda(nodo)
        return nodo

    def altura(self):
        return self._alt(self.raiz)

    def buscar(self, valor):
        actual, pasos = self.raiz, 0
        while actual is not None:
            pasos += 1
            if valor == actual.valor:
                return True, pasos
            actual = actual.izquierdo if valor < actual.valor else actual.derecho
        return False, pasos

    def inorden(self):
        resultado, pila, actual = [], [], self.raiz
        while pila or actual:
            while actual:
                pila.append(actual)
                actual = actual.izquierdo
            actual = pila.pop()
            resultado.append(actual.valor)
            actual = actual.derecho
        return resultado

    def por_niveles(self):
        if self.raiz is None:
            return []
        resultado, cola, i = [], [self.raiz], 0
        while i < len(cola):
            nodo = cola[i]
            i += 1
            resultado.append(nodo.valor)
            if nodo.izquierdo:
                cola.append(nodo.izquierdo)
            if nodo.derecho:
                cola.append(nodo.derecho)
        return resultado
