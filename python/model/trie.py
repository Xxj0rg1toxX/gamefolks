"""
MODELO - Trie para autocompletado (Top-K por popularidad) + footprint de memoria.
Une trie_autocompletado.py y reto2_trie_topk_memoria.py.
"""
import sys


class NodoTrie:
    def __init__(self):
        self.hijos = {}
        self.es_fin_de_palabra = False
        self.nombre_completo = None
        self.popularidad = 0


class Trie:
    def __init__(self):
        self.raiz = NodoTrie()
        self.total_palabras = 0

    def insertar(self, nombre, popularidad=0):
        actual = self.raiz
        for c in nombre.lower():
            if c not in actual.hijos:
                actual.hijos[c] = NodoTrie()
            actual = actual.hijos[c]
        if not actual.es_fin_de_palabra:
            self.total_palabras += 1
        actual.es_fin_de_palabra = True
        actual.nombre_completo = nombre
        actual.popularidad = popularidad

    def _nodo_del_prefijo(self, prefijo):
        actual = self.raiz
        for c in prefijo.lower():
            if c not in actual.hijos:
                return None
            actual = actual.hijos[c]
        return actual

    def _recolectar(self, nodo, resultados):
        if nodo.es_fin_de_palabra:
            resultados.append((nodo.nombre_completo, nodo.popularidad))
        for h in nodo.hijos.values():
            self._recolectar(h, resultados)

    def buscar_por_prefijo(self, prefijo, maximo=10):
        """Autocompletado simple (orden de insercion del DFS), sin popularidad."""
        nodo = self._nodo_del_prefijo(prefijo)
        if nodo is None:
            return []
        todos = []
        self._recolectar(nodo, todos)
        return [n for n, _ in todos][:maximo]

    def autocompletar_top_k(self, prefijo, k=5, minimo=2):
        """Top-K por popularidad. Lanza ValueError si el prefijo es muy corto."""
        if len(prefijo) < minimo:
            raise ValueError(f"Escribe al menos {minimo} caracteres para autocompletar.")
        nodo = self._nodo_del_prefijo(prefijo)
        if nodo is None:
            return []
        candidatos = []
        self._recolectar(nodo, candidatos)
        return sorted(candidatos, key=lambda p: p[1], reverse=True)[:k]

    def listar_todo(self):
        todos = []
        self._recolectar(self.raiz, todos)
        return [n for n, _ in todos]

    def contar_nodos(self):
        total, pila = 0, [self.raiz]
        while pila:
            n = pila.pop()
            total += 1
            pila.extend(n.hijos.values())
        return total


# ---------- medicion de memoria real ----------
def memoria_trie_en_bytes(trie):
    total, pendientes = 0, [trie.raiz]
    while pendientes:
        nodo = pendientes.pop()
        total += sys.getsizeof(nodo) + sys.getsizeof(nodo.hijos)
        for c, h in nodo.hijos.items():
            total += sys.getsizeof(c)
            pendientes.append(h)
        if nodo.nombre_completo:
            total += sys.getsizeof(nodo.nombre_completo)
    return total


def memoria_lista_en_bytes(nombres):
    return sys.getsizeof(nombres) + sum(sys.getsizeof(n) for n in nombres)


def memoria_set_en_bytes(nombres):
    conj = set(nombres)
    return sys.getsizeof(conj) + sum(sys.getsizeof(n) for n in conj)
